"""Independent reference-model tests for the standalone work-RAM fault API."""
import ctypes
import itertools
import random
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAM_BYTES = 65_536
WORDS = RAM_BYTES // 2

STATUS_OK = 0
STATUS_INVALID_ARGUMENT = 1
STATUS_SHORT_BUFFER = 2
STATUS_OUT_OF_BOUNDS = 3
STATUS_MISALIGNED = 4
STATUS_INVALID_CONFIG = 5

KIND_NONE = 0
KIND_ADDRESS = 1
KIND_DATA = 2
ACCESS_NONE = 0
ACCESS_READ = 1
ACCESS_WRITE = 2
ACCESS_BOTH = 3


class Config(ctypes.Structure):
    _fields_ = [
        ("kind", ctypes.c_int),
        ("access", ctypes.c_int),
        ("line_a", ctypes.c_uint8),
        ("line_b", ctypes.c_uint8),
    ]


class WorkRamFaultProperties(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build_dir = tempfile.TemporaryDirectory(prefix="work-ram-properties-")
        suffix = ".dylib" if sys.platform == "darwin" else ".so"
        cls.library_path = Path(cls.build_dir.name) / f"libwork_ram_fault{suffix}"
        shared_flag = "-dynamiclib" if sys.platform == "darwin" else "-shared"
        subprocess.run(
            [
                "cc", "-std=c11", "-Wall", "-Wextra", "-Werror", "-fPIC", shared_flag,
                str(ROOT / "scripts/work_ram_fault.c"), "-o", str(cls.library_path),
            ],
            check=True,
            cwd=ROOT,
        )
        cls.lib = ctypes.CDLL(str(cls.library_path))
        cls.lib.work_ram_fault_clear.restype = Config
        cls.lib.work_ram_fault_validate.argtypes = [ctypes.POINTER(Config)]
        cls.lib.work_ram_fault_validate.restype = ctypes.c_int
        cls.lib.work_ram_fault_read_word.argtypes = [
            ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.c_uint32,
            ctypes.POINTER(Config), ctypes.POINTER(ctypes.c_uint16),
        ]
        cls.lib.work_ram_fault_read_word.restype = ctypes.c_int
        cls.lib.work_ram_fault_write_word.argtypes = [
            ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.c_uint32,
            ctypes.POINTER(Config), ctypes.c_uint16,
        ]
        cls.lib.work_ram_fault_write_word.restype = ctypes.c_int
        cls.addClassCleanup(cls.build_dir.cleanup)

    @staticmethod
    def config(kind, access, line_a=0, line_b=0):
        return Config(kind, access, line_a, line_b)

    @staticmethod
    def memory(data=None, size=RAM_BYTES):
        if data is None:
            data = bytearray(size)
        return data, (ctypes.c_uint8 * len(data)).from_buffer(data)

    @staticmethod
    def word(memory, address):
        return (memory[address] << 8) | memory[address + 1]

    @staticmethod
    def put_word(memory, address, value):
        memory[address] = (value >> 8) & 0xFF
        memory[address + 1] = value & 0xFF

    @staticmethod
    def project(value, line_a, line_b):
        pair = (1 << line_a) | (1 << line_b)
        return value if value & pair == pair else value & ~pair

    @staticmethod
    def pattern(word_address):
        # Odd multiplication makes the initial 16-bit word values distinct.
        return (word_address * 0x9E37 + 0x1234) & 0xFFFF

    @classmethod
    def patterned_memory(cls):
        data = bytearray(RAM_BYTES)
        for word_address in range(WORDS):
            cls.put_word(data, word_address * 2, cls.pattern(word_address))
        return data

    def test_no_fault_big_endian_round_trip_and_determinism(self):
        backing, memory = self.memory()
        clear = self.lib.work_ram_fault_clear()

        for word_address in range(WORDS):
            byte_address = word_address * 2
            value = (word_address * 0xBEEF + 0x5A3C) & 0xFFFF
            self.assertEqual(
                self.lib.work_ram_fault_write_word(memory, RAM_BYTES, byte_address, ctypes.byref(clear), value),
                STATUS_OK,
            )
            self.assertEqual(backing[byte_address:byte_address + 2], bytes([value >> 8, value & 0xFF]))
            for _ in range(2):
                result = ctypes.c_uint16(0xFFFF)
                self.assertEqual(
                    self.lib.work_ram_fault_read_word(
                        memory, RAM_BYTES, byte_address, ctypes.byref(clear), ctypes.byref(result)),
                    STATUS_OK,
                )
                self.assertEqual(result.value, value)

    def test_every_address_bridge_pair_and_all_four_bit_states(self):
        for line_a, line_b in itertools.combinations(range(15), 2):
            for state_a, state_b in itertools.product((0, 1), repeat=2):
                # Vary all non-pair address bits deterministically as well.
                source = ((line_a * 7919 + line_b * 1013 + state_a * 431 + state_b * 977) & 0x7FFF)
                pair_mask = (1 << line_a) | (1 << line_b)
                source = (source & ~pair_mask) | (state_a << line_a) | (state_b << line_b)
                target = self.project(source, line_a, line_b)
                byte_address = source * 2
                target_byte_address = target * 2

                read_config = self.config(KIND_ADDRESS, ACCESS_READ, line_a, line_b)
                original = self.patterned_memory()
                before = bytes(original)
                backing, memory = self.memory(original)
                result = ctypes.c_uint16(0)
                self.assertEqual(
                    self.lib.work_ram_fault_read_word(
                        memory, RAM_BYTES, byte_address, ctypes.byref(read_config), ctypes.byref(result)),
                    STATUS_OK,
                )
                self.assertEqual(result.value, self.pattern(target))
                self.assertEqual(bytes(backing), before, "address-fault read mutated RAM")

                write_config = self.config(KIND_ADDRESS, ACCESS_WRITE, line_a, line_b)
                expected = bytearray(before)
                write_value = (0xA55A ^ source * 257) & 0xFFFF
                self.assertEqual(
                    self.lib.work_ram_fault_write_word(
                        memory, RAM_BYTES, byte_address, ctypes.byref(write_config), write_value),
                    STATUS_OK,
                )
                self.put_word(expected, target_byte_address, write_value)
                self.assertEqual(bytes(backing), bytes(expected), "address write changed bytes outside its alias")
                clear = self.lib.work_ram_fault_clear()
                persisted = ctypes.c_uint16(0)
                self.assertEqual(
                    self.lib.work_ram_fault_read_word(
                        memory, RAM_BYTES, target_byte_address, ctypes.byref(clear), ctypes.byref(persisted)),
                    STATUS_OK,
                )
                self.assertEqual(persisted.value, write_value, "fault removal erased an address alias write")

                both = self.config(KIND_ADDRESS, ACCESS_BOTH, line_a, line_b)
                both_memory = self.patterned_memory()
                both_backing, both_ptr = self.memory(both_memory)
                both_value = (0x3CC3 ^ source * 17) & 0xFFFF
                self.assertEqual(
                    self.lib.work_ram_fault_write_word(
                        both_ptr, RAM_BYTES, byte_address, ctypes.byref(both), both_value),
                    STATUS_OK,
                )
                readback = ctypes.c_uint16(0)
                self.assertEqual(
                    self.lib.work_ram_fault_read_word(
                        both_ptr, RAM_BYTES, byte_address, ctypes.byref(both), ctypes.byref(readback)),
                    STATUS_OK,
                )
                self.assertEqual(readback.value, both_value)
                self.assertEqual(self.word(both_backing, target_byte_address), both_value)

                # A fault selected for the other operation must not apply.
                write_only_read = ctypes.c_uint16(0)
                self.assertEqual(
                    self.lib.work_ram_fault_read_word(
                        memory, RAM_BYTES, byte_address, ctypes.byref(write_config),
                        ctypes.byref(write_only_read)),
                    STATUS_OK,
                )
                self.assertEqual(write_only_read.value, self.word(backing, byte_address))

    def test_every_data_bridge_pair_and_all_four_bit_states(self):
        for line_a, line_b in itertools.combinations(range(16), 2):
            pair_mask = (1 << line_a) | (1 << line_b)
            for state_a, state_b in itertools.product((0, 1), repeat=2):
                state = (state_a << line_a) | (state_b << line_b)
                for variation in (0x0000, 0x5555, 0xAAAA, 0xFFFF):
                    value = (variation & ~pair_mask) | state
                    projected = self.project(value, line_a, line_b)
                    backing, memory = self.memory(bytearray([value >> 8, value & 0xFF]) + bytearray(RAM_BYTES - 2))
                    before = bytes(backing)

                    read_config = self.config(KIND_DATA, ACCESS_READ, line_a, line_b)
                    result = ctypes.c_uint16(0)
                    self.assertEqual(
                        self.lib.work_ram_fault_read_word(
                            memory, RAM_BYTES, 0, ctypes.byref(read_config), ctypes.byref(result)),
                        STATUS_OK,
                    )
                    self.assertEqual(result.value, projected)
                    self.assertEqual(bytes(backing), before, "data-fault read mutated RAM")

                    write_config = self.config(KIND_DATA, ACCESS_WRITE, line_a, line_b)
                    self.assertEqual(
                        self.lib.work_ram_fault_write_word(
                            memory, RAM_BYTES, 0, ctypes.byref(write_config), value),
                        STATUS_OK,
                    )
                    self.assertEqual(self.word(backing, 0), projected)
                    clear = self.lib.work_ram_fault_clear()
                    persisted = ctypes.c_uint16(0)
                    self.assertEqual(
                        self.lib.work_ram_fault_read_word(
                            memory, RAM_BYTES, 0, ctypes.byref(clear), ctypes.byref(persisted)),
                        STATUS_OK,
                    )
                    self.assertEqual(persisted.value, projected, "fault removal erased a projected data write")

                    both = self.config(KIND_DATA, ACCESS_BOTH, line_a, line_b)
                    both_value = value ^ 0xF00F
                    self.assertEqual(
                        self.lib.work_ram_fault_write_word(
                            memory, RAM_BYTES, 2, ctypes.byref(both), both_value),
                        STATUS_OK,
                    )
                    both_read = ctypes.c_uint16(0)
                    self.assertEqual(
                        self.lib.work_ram_fault_read_word(
                            memory, RAM_BYTES, 2, ctypes.byref(both), ctypes.byref(both_read)),
                        STATUS_OK,
                    )
                    both_projected = self.project(both_value, line_a, line_b)
                    self.assertEqual(both_read.value, both_projected)
                    self.assertEqual(self.word(backing, 2), both_projected)

                    # Read-only configuration cannot alter a write.
                    read_only = self.config(KIND_DATA, ACCESS_READ, line_a, line_b)
                    self.assertEqual(
                        self.lib.work_ram_fault_write_word(
                            memory, RAM_BYTES, 4, ctypes.byref(read_only), value),
                        STATUS_OK,
                    )
                    self.assertEqual(self.word(backing, 4), value)
                    write_only = self.config(KIND_DATA, ACCESS_WRITE, line_a, line_b)
                    write_only_read = ctypes.c_uint16(0)
                    self.assertEqual(
                        self.lib.work_ram_fault_read_word(
                            memory, RAM_BYTES, 4, ctypes.byref(write_only),
                            ctypes.byref(write_only_read)),
                        STATUS_OK,
                    )
                    self.assertEqual(write_only_read.value, value)

    def test_invalid_configurations_and_transactions_do_not_mutate(self):
        self.assertEqual(self.lib.work_ram_fault_validate(None), STATUS_INVALID_ARGUMENT)
        invalid_configs = [
            self.config(KIND_NONE, ACCESS_READ),
            self.config(KIND_NONE, ACCESS_NONE, 1, 0),
            self.config(KIND_ADDRESS, ACCESS_NONE, 0, 1),
            self.config(KIND_ADDRESS, ACCESS_BOTH, 0, 0),
            self.config(KIND_ADDRESS, ACCESS_READ, 0, 15),
            self.config(KIND_DATA, ACCESS_WRITE, 0, 16),
            self.config(KIND_DATA, ACCESS_BOTH, 16, 17),
            self.config(99, ACCESS_BOTH, 0, 1),
        ]
        for config in invalid_configs:
            self.assertEqual(self.lib.work_ram_fault_validate(ctypes.byref(config)), STATUS_INVALID_CONFIG)

        data = bytearray((index * 29 + 7) & 0xFF for index in range(RAM_BYTES))
        before = bytes(data)
        backing, memory = self.memory(data)
        clear = self.lib.work_ram_fault_clear()
        invalid = self.config(KIND_DATA, ACCESS_WRITE, 3, 3)
        result = ctypes.c_uint16(0xBEEF)
        bad_reads = [
            (memory, RAM_BYTES, 0, ctypes.byref(invalid), ctypes.byref(result), STATUS_INVALID_CONFIG),
            (memory, RAM_BYTES - 1, 0, ctypes.byref(clear), ctypes.byref(result), STATUS_SHORT_BUFFER),
            (memory, RAM_BYTES, 1, ctypes.byref(clear), ctypes.byref(result), STATUS_MISALIGNED),
            (memory, RAM_BYTES, RAM_BYTES - 1, ctypes.byref(clear), ctypes.byref(result), STATUS_OUT_OF_BOUNDS),
            (memory, RAM_BYTES, RAM_BYTES, ctypes.byref(clear), ctypes.byref(result), STATUS_OUT_OF_BOUNDS),
            (memory, RAM_BYTES, 0xFFFFFFFF, ctypes.byref(clear), ctypes.byref(result), STATUS_OUT_OF_BOUNDS),
            (None, RAM_BYTES, 0, ctypes.byref(clear), ctypes.byref(result), STATUS_INVALID_ARGUMENT),
            (memory, RAM_BYTES, 0, ctypes.byref(clear), None, STATUS_INVALID_ARGUMENT),
        ]
        for args in bad_reads:
            result.value = 0xBEEF
            self.assertEqual(self.lib.work_ram_fault_read_word(*args[:-1]), args[-1])
            self.assertEqual(result.value, 0xBEEF, "failed read modified its output")

        bad_writes = [
            (memory, RAM_BYTES, 0, ctypes.byref(invalid), 0x1234, STATUS_INVALID_CONFIG),
            (memory, RAM_BYTES - 1, 0, ctypes.byref(clear), 0x1234, STATUS_SHORT_BUFFER),
            (memory, RAM_BYTES, 1, ctypes.byref(clear), 0x1234, STATUS_MISALIGNED),
            (memory, RAM_BYTES, RAM_BYTES - 1, ctypes.byref(clear), 0x1234, STATUS_OUT_OF_BOUNDS),
            (memory, RAM_BYTES, RAM_BYTES, ctypes.byref(clear), 0x1234, STATUS_OUT_OF_BOUNDS),
            (None, RAM_BYTES, 0, ctypes.byref(clear), 0x1234, STATUS_INVALID_ARGUMENT),
        ]
        for args in bad_writes:
            self.assertEqual(self.lib.work_ram_fault_write_word(*args[:-1]), args[-1])
            self.assertEqual(bytes(backing), before, "failed write mutated RAM")

    def test_access_boundaries_and_oversized_buffer_tail(self):
        data = bytearray([0x5A] * (RAM_BYTES + 16))
        backing, memory = self.memory(data)
        clear = self.lib.work_ram_fault_clear()
        final_value = 0xA17C
        self.assertEqual(
            self.lib.work_ram_fault_write_word(
                memory, len(backing), RAM_BYTES - 2, ctypes.byref(clear), final_value),
            STATUS_OK,
        )
        self.assertEqual(backing[RAM_BYTES - 2:RAM_BYTES], bytes([0xA1, 0x7C]))
        self.assertEqual(backing[RAM_BYTES:], bytes([0x5A] * 16))
        result = ctypes.c_uint16(0)
        self.assertEqual(
            self.lib.work_ram_fault_read_word(
                memory, len(backing), RAM_BYTES - 2, ctypes.byref(clear), ctypes.byref(result)),
            STATUS_OK,
        )
        self.assertEqual(result.value, final_value)


if __name__ == "__main__":
    unittest.main(verbosity=2)
