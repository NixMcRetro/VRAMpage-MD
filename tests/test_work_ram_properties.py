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
STATUS_UNSUPPORTED_LANE = 6

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
        cls.lib.work_ram_fault_map_word_address.argtypes = [
            ctypes.c_uint16, ctypes.POINTER(Config), ctypes.c_int,
            ctypes.POINTER(ctypes.c_uint16),
        ]
        cls.lib.work_ram_fault_map_word_address.restype = ctypes.c_int
        cls.lib.work_ram_fault_map_byte_address.argtypes = [
            ctypes.c_uint32, ctypes.POINTER(Config), ctypes.c_int,
            ctypes.POINTER(ctypes.c_uint32),
        ]
        cls.lib.work_ram_fault_map_byte_address.restype = ctypes.c_int
        cls.lib.work_ram_fault_project_word.argtypes = [
            ctypes.c_uint16, ctypes.POINTER(Config), ctypes.c_int,
            ctypes.POINTER(ctypes.c_uint16),
        ]
        cls.lib.work_ram_fault_project_word.restype = ctypes.c_int
        cls.lib.work_ram_fault_project_byte.argtypes = [
            ctypes.c_uint8, ctypes.c_uint32, ctypes.POINTER(Config), ctypes.c_int,
            ctypes.POINTER(ctypes.c_uint8),
        ]
        cls.lib.work_ram_fault_project_byte.restype = ctypes.c_int
        cls.lib.work_ram_fault_read_byte.argtypes = [
            ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.c_uint32,
            ctypes.POINTER(Config), ctypes.POINTER(ctypes.c_uint8),
        ]
        cls.lib.work_ram_fault_read_byte.restype = ctypes.c_int
        cls.lib.work_ram_fault_write_byte.argtypes = [
            ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.c_uint32,
            ctypes.POINTER(Config), ctypes.c_uint8,
        ]
        cls.lib.work_ram_fault_write_byte.restype = ctypes.c_int
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
    def project_byte(value, line_a, line_b):
        return WorkRamFaultProperties.project(value, line_a % 8, line_b % 8)

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

    def test_no_fault_byte_round_trip_visits_every_address(self):
        backing, memory = self.memory()
        clear = self.lib.work_ram_fault_clear()
        for byte_address in range(RAM_BYTES):
            value = (byte_address * 173 + 0xA5) & 0xFF
            self.assertEqual(
                self.lib.work_ram_fault_write_byte(
                    memory, RAM_BYTES, byte_address, ctypes.byref(clear), value),
                STATUS_OK,
            )
            self.assertEqual(backing[byte_address], value)
            observed = ctypes.c_uint8(0)
            self.assertEqual(
                self.lib.work_ram_fault_read_byte(
                    memory, RAM_BYTES, byte_address, ctypes.byref(clear), ctypes.byref(observed)),
                STATUS_OK,
            )
            self.assertEqual(observed.value, value)

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

    def test_byte_address_mapping_exhausts_pairs_and_preserves_a0(self):
        clear = self.lib.work_ram_fault_clear()
        for byte_address in range(RAM_BYTES):
            mapped = ctypes.c_uint32(0xFFFFFFFF)
            self.assertEqual(
                self.lib.work_ram_fault_map_byte_address(
                    byte_address, ctypes.byref(clear), ACCESS_READ, ctypes.byref(mapped)),
                STATUS_OK,
            )
            self.assertEqual(mapped.value, byte_address)

        for line_a, line_b in itertools.combinations(range(15), 2):
            pair_mask = (1 << line_a) | (1 << line_b)
            for state_a, state_b, lane in itertools.product((0, 1), (0, 1), (0, 1)):
                source_word = (line_a * 701 + line_b * 313 + state_a * 4099 + state_b * 1987) & 0x7FFF
                source_word = (source_word & ~pair_mask) | (state_a << line_a) | (state_b << line_b)
                target_word = self.project(source_word, line_a, line_b)
                source_byte = source_word * 2 + lane
                target_byte = target_word * 2 + lane

                read_fault = self.config(KIND_ADDRESS, ACCESS_READ, line_a, line_b)
                mapped = ctypes.c_uint32(0xFFFFFFFF)
                self.assertEqual(
                    self.lib.work_ram_fault_map_byte_address(
                        source_byte, ctypes.byref(read_fault), ACCESS_READ, ctypes.byref(mapped)),
                    STATUS_OK,
                )
                self.assertEqual(mapped.value, target_byte)
                self.assertEqual(mapped.value & 1, lane, "A0 must keep the original byte lane")

                # Access direction is explicit at the helper boundary.
                unchanged = ctypes.c_uint32(0xFFFFFFFF)
                self.assertEqual(
                    self.lib.work_ram_fault_map_byte_address(
                        source_byte, ctypes.byref(read_fault), ACCESS_WRITE, ctypes.byref(unchanged)),
                    STATUS_OK,
                )
                self.assertEqual(unchanged.value, source_byte)

                write_fault = self.config(KIND_ADDRESS, ACCESS_WRITE, line_a, line_b)
                mapped_write = ctypes.c_uint32(0xFFFFFFFF)
                self.assertEqual(
                    self.lib.work_ram_fault_map_byte_address(
                        source_byte, ctypes.byref(write_fault), ACCESS_WRITE,
                        ctypes.byref(mapped_write)),
                    STATUS_OK,
                )
                self.assertEqual(mapped_write.value, target_byte)

                backing = bytearray(RAM_BYTES)
                backing[source_byte] = 0x31
                backing[target_byte] = 0x92
                before = bytes(backing)
                memory = (ctypes.c_uint8 * RAM_BYTES).from_buffer(backing)
                observed = ctypes.c_uint8(0)
                self.assertEqual(
                    self.lib.work_ram_fault_read_byte(
                        memory, RAM_BYTES, source_byte, ctypes.byref(read_fault),
                        ctypes.byref(observed)),
                    STATUS_OK,
                )
                self.assertEqual(observed.value, backing[target_byte])
                self.assertEqual(bytes(backing), before, "address-fault byte read mutated RAM")

                stored = 0xC7 ^ (source_word & 0xFF)
                self.assertEqual(
                    self.lib.work_ram_fault_write_byte(
                        memory, RAM_BYTES, source_byte, ctypes.byref(write_fault), stored),
                    STATUS_OK,
                )
                self.assertEqual(backing[target_byte], stored)
                if target_byte != source_byte:
                    self.assertEqual(backing[source_byte], 0x31)
                clear_read = ctypes.c_uint8(0)
                self.assertEqual(
                    self.lib.work_ram_fault_read_byte(
                        memory, RAM_BYTES, target_byte, ctypes.byref(clear),
                        ctypes.byref(clear_read)),
                    STATUS_OK,
                )
                self.assertEqual(clear_read.value, stored, "address-fault byte write did not persist")

                both_fault = self.config(KIND_ADDRESS, ACCESS_BOTH, line_a, line_b)
                both_backing = bytearray(RAM_BYTES)
                both_memory = (ctypes.c_uint8 * RAM_BYTES).from_buffer(both_backing)
                both_value = 0x5D ^ (source_word & 0xFF)
                self.assertEqual(
                    self.lib.work_ram_fault_write_byte(
                        both_memory, RAM_BYTES, source_byte, ctypes.byref(both_fault), both_value),
                    STATUS_OK,
                )
                both_observed = ctypes.c_uint8(0)
                self.assertEqual(
                    self.lib.work_ram_fault_read_byte(
                        both_memory, RAM_BYTES, source_byte, ctypes.byref(both_fault),
                        ctypes.byref(both_observed)),
                    STATUS_OK,
                )
                self.assertEqual(both_observed.value, both_value)
                self.assertEqual(both_backing[target_byte], both_value)

    def test_byte_data_pairs_follow_physical_lanes(self):
        lane_states = (0x00, 0x01, 0x55, 0x80, 0xAA, 0xFF)
        for line_a, line_b in itertools.combinations(range(16), 2):
            same_lane = (line_a < 8) == (line_b < 8)
            selected_lane = 1 if line_a < 8 else 0  # lower D0..D7 is odd; upper D8..D15 is even
            for lane in (0, 1):
                address = 0x1040 + lane
                fault = self.config(KIND_DATA, ACCESS_BOTH, line_a, line_b)
                for value in lane_states:
                    expected = self.project_byte(value, line_a, line_b)
                    projected = ctypes.c_uint8(0xCC)
                    status = self.lib.work_ram_fault_project_byte(
                        value, address, ctypes.byref(fault), ACCESS_READ, ctypes.byref(projected))
                    if same_lane and lane == selected_lane:
                        self.assertEqual(status, STATUS_OK)
                        self.assertEqual(projected.value, expected)
                    elif same_lane:
                        self.assertEqual(status, STATUS_OK, "same-lane fault should be identity on the other lane")
                        self.assertEqual(projected.value, value)
                    else:
                        self.assertEqual(status, STATUS_UNSUPPORTED_LANE)
                        self.assertEqual(projected.value, 0xCC, "unsupported projection changed its output")

                # Same-lane pairs are usable on their own lane and identity on the other.
                # Cross-lane pairs are rejected by active byte reads and writes.
                backing = bytearray([0x6D] * RAM_BYTES)
                backing[address] = 0xA5
                memory = (ctypes.c_uint8 * RAM_BYTES).from_buffer(backing)
                read_config = self.config(KIND_DATA, ACCESS_READ, line_a, line_b)
                read_value = ctypes.c_uint8(0xF3)
                before = bytes(backing)
                status = self.lib.work_ram_fault_read_byte(
                    memory, RAM_BYTES, address, ctypes.byref(read_config), ctypes.byref(read_value))
                if not same_lane:
                    self.assertEqual(status, STATUS_UNSUPPORTED_LANE)
                    self.assertEqual(read_value.value, 0xF3)
                    self.assertEqual(bytes(backing), before)
                else:
                    self.assertEqual(status, STATUS_OK)
                    expected = self.project_byte(0xA5, line_a, line_b) if lane == selected_lane else 0xA5
                    self.assertEqual(read_value.value, expected)
                    self.assertEqual(bytes(backing), before)

                write_config = self.config(KIND_DATA, ACCESS_WRITE, line_a, line_b)
                write_value = 0x96
                before = bytes(backing)
                status = self.lib.work_ram_fault_write_byte(
                    memory, RAM_BYTES, address, ctypes.byref(write_config), write_value)
                if not same_lane:
                    self.assertEqual(status, STATUS_UNSUPPORTED_LANE)
                    self.assertEqual(bytes(backing), before, "unsupported byte write mutated RAM")
                else:
                    self.assertEqual(status, STATUS_OK)
                    expected = self.project_byte(write_value, line_a, line_b) if lane == selected_lane else write_value
                    self.assertEqual(backing[address], expected)
                    if lane == selected_lane:
                        clear = self.lib.work_ram_fault_clear()
                        persisted = ctypes.c_uint8(0)
                        self.assertEqual(
                            self.lib.work_ram_fault_read_byte(
                                memory, RAM_BYTES, address, ctypes.byref(clear), ctypes.byref(persisted)),
                            STATUS_OK,
                        )
                        self.assertEqual(persisted.value, expected, "data-lane write vanished after fault clear")

                # BOTH applies to the selected physical lane, but stays identity
                # on the other lane for a same-lane pair.
                if same_lane:
                    both = self.config(KIND_DATA, ACCESS_BOTH, line_a, line_b)
                    both_address = 0x3040 + selected_lane
                    both_value = 0xB6
                    self.assertEqual(
                        self.lib.work_ram_fault_write_byte(
                            memory, RAM_BYTES, both_address, ctypes.byref(both), both_value),
                        STATUS_OK,
                    )
                    both_expected = self.project_byte(both_value, line_a, line_b)
                    both_result = ctypes.c_uint8(0)
                    self.assertEqual(
                        self.lib.work_ram_fault_read_byte(
                            memory, RAM_BYTES, both_address, ctypes.byref(both),
                            ctypes.byref(both_result)),
                        STATUS_OK,
                    )
                    self.assertEqual(both_result.value, both_expected)
                    self.assertEqual(backing[both_address], both_expected)

                    other_lane = both_address ^ 1
                    self.assertEqual(
                        self.lib.work_ram_fault_write_byte(
                            memory, RAM_BYTES, other_lane, ctypes.byref(both), 0xE1),
                        STATUS_OK,
                    )
                    self.assertEqual(backing[other_lane], 0xE1)
                    other_result = ctypes.c_uint8(0)
                    self.assertEqual(
                        self.lib.work_ram_fault_read_byte(
                            memory, RAM_BYTES, other_lane, ctypes.byref(both),
                            ctypes.byref(other_result)),
                        STATUS_OK,
                    )
                    self.assertEqual(other_result.value, 0xE1)

    def test_cross_lane_faults_reject_only_active_directions(self):
        for line_a in range(8):
            for line_b in range(8, 16):
                for access in (ACCESS_READ, ACCESS_WRITE, ACCESS_BOTH):
                    config = self.config(KIND_DATA, access, line_a, line_b)
                    for address in (0x2000, 0x2001):
                        backing = bytearray([0x73] * RAM_BYTES)
                        memory = (ctypes.c_uint8 * RAM_BYTES).from_buffer(backing)
                        read_result = ctypes.c_uint8(0xD4)
                        before = bytes(backing)
                        read_status = self.lib.work_ram_fault_read_byte(
                            memory, RAM_BYTES, address, ctypes.byref(config), ctypes.byref(read_result))
                        read_active = access in (ACCESS_READ, ACCESS_BOTH)
                        if read_active:
                            self.assertEqual(read_status, STATUS_UNSUPPORTED_LANE)
                            self.assertEqual(read_result.value, 0xD4)
                            self.assertEqual(bytes(backing), before)
                        else:
                            self.assertEqual(read_status, STATUS_OK)
                            self.assertEqual(read_result.value, 0x73)

                        write_status = self.lib.work_ram_fault_write_byte(
                            memory, RAM_BYTES, address, ctypes.byref(config), 0xA6)
                        write_active = access in (ACCESS_WRITE, ACCESS_BOTH)
                        if write_active:
                            self.assertEqual(write_status, STATUS_UNSUPPORTED_LANE)
                            self.assertEqual(bytes(backing), before, "unsupported byte write mutated RAM")
                        else:
                            self.assertEqual(write_status, STATUS_OK)
                            self.assertEqual(backing[address], 0xA6)

    def test_byte_api_bounds_fail_without_output_or_storage_mutation(self):
        backing = bytearray([0x5C] * (RAM_BYTES + 8))
        memory = (ctypes.c_uint8 * len(backing)).from_buffer(backing)
        clear = self.lib.work_ram_fault_clear()
        result = ctypes.c_uint8(0xB7)

        # Both physical endpoints are valid byte transactions.
        for address, value in ((0, 0x12), (RAM_BYTES - 1, 0xE8)):
            self.assertEqual(
                self.lib.work_ram_fault_write_byte(
                    memory, len(backing), address, ctypes.byref(clear), value),
                STATUS_OK,
            )
            self.assertEqual(backing[address], value)
            result.value = 0
            self.assertEqual(
                self.lib.work_ram_fault_read_byte(
                    memory, len(backing), address, ctypes.byref(clear), ctypes.byref(result)),
                STATUS_OK,
            )
            self.assertEqual(result.value, value)

        before = bytes(backing)
        invalid = self.config(KIND_DATA, ACCESS_BOTH, 4, 4)
        for address in (RAM_BYTES, RAM_BYTES + 1, 0xFFFFFFFF):
            result.value = 0xB7
            self.assertEqual(
                self.lib.work_ram_fault_read_byte(
                    memory, len(backing), address, ctypes.byref(clear), ctypes.byref(result)),
                STATUS_OUT_OF_BOUNDS,
            )
            self.assertEqual(result.value, 0xB7)
            self.assertEqual(
                self.lib.work_ram_fault_write_byte(
                    memory, len(backing), address, ctypes.byref(clear), 0xAB),
                STATUS_OUT_OF_BOUNDS,
            )
            self.assertEqual(bytes(backing), before)

        self.assertEqual(
            self.lib.work_ram_fault_read_byte(
                memory, RAM_BYTES - 1, 0, ctypes.byref(clear), ctypes.byref(result)),
            STATUS_SHORT_BUFFER,
        )
        self.assertEqual(
            self.lib.work_ram_fault_write_byte(memory, RAM_BYTES - 1, 0, ctypes.byref(clear), 0xAA),
            STATUS_SHORT_BUFFER,
        )
        self.assertEqual(
            self.lib.work_ram_fault_read_byte(memory, len(backing), 0, ctypes.byref(invalid), ctypes.byref(result)),
            STATUS_INVALID_CONFIG,
        )
        self.assertEqual(
            self.lib.work_ram_fault_write_byte(memory, len(backing), 0, ctypes.byref(invalid), 0xAA),
            STATUS_INVALID_CONFIG,
        )
        self.assertEqual(bytes(backing), before)

        mapped = ctypes.c_uint32(0x12345678)
        self.assertEqual(
            self.lib.work_ram_fault_map_byte_address(
                RAM_BYTES, ctypes.byref(clear), ACCESS_READ, ctypes.byref(mapped)),
            STATUS_OUT_OF_BOUNDS,
        )
        self.assertEqual(mapped.value, 0x12345678)
        self.assertEqual(
            self.lib.work_ram_fault_map_byte_address(RAM_BYTES, ctypes.byref(clear), ACCESS_READ, None),
            STATUS_INVALID_ARGUMENT,
        )
        projected = ctypes.c_uint8(0x6A)
        self.assertEqual(
            self.lib.work_ram_fault_project_byte(
                0xFF, RAM_BYTES, ctypes.byref(clear), ACCESS_READ, ctypes.byref(projected)),
            STATUS_OUT_OF_BOUNDS,
        )
        self.assertEqual(projected.value, 0x6A)

        no_data = ctypes.c_uint8(0xB7)
        self.assertEqual(
            self.lib.work_ram_fault_read_byte(memory, len(backing), 0, ctypes.byref(clear), None),
            STATUS_INVALID_ARGUMENT,
        )
        self.assertEqual(
            self.lib.work_ram_fault_read_byte(None, len(backing), 0, ctypes.byref(clear), ctypes.byref(no_data)),
            STATUS_INVALID_ARGUMENT,
        )
        self.assertEqual(no_data.value, 0xB7)
        self.assertEqual(
            self.lib.work_ram_fault_write_byte(None, len(backing), 0, ctypes.byref(clear), 0xAA),
            STATUS_INVALID_ARGUMENT,
        )
        self.assertEqual(bytes(backing), before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
