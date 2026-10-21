"""Golden reference mapping tests for the deterministic 64 KiB Mode 5 net model."""
import unittest


def pair(address, x, y):
    mask = (1 << x) | (1 << y)
    return address if (address & mask) == mask else (address & ~mask)


def map_address(address, a, b):
    value = pair(address, a + 2, b + 2)
    ca = a if a < 2 else a + 8
    cb = b if b < 2 else b + 8
    return pair(value, ca, cb) & 0xFFFF


class PhysicalAddressTests(unittest.TestCase):
    def test_dual_phase_AD0_AD1(self):
        # AD0/AD1 are A2/A3 in row and A0/A1 in column phase.
        self.assertEqual(map_address(0b1111, 0, 1), 0b1111)
        self.assertEqual(map_address(0b0101, 0, 1), 0)
        self.assertEqual(map_address(0b1010, 0, 1), 0)

    def test_high_physical_lines(self):
        # AD6↔AD7 affects row A8/A9, column A14/A15.
        original = 0xC300
        self.assertEqual(map_address(original, 6, 7), original)
        self.assertEqual(map_address(0x8100, 6, 7), 0x0000)

    def test_no_new_one_bits(self):
        for a in range(8):
            for b in range(a+1, 8):
                for x in [0, 1, 0x55AA, 0xA5A5, 0xFFFF, 0xC001, 0xBEEF]:
                    val = map_address(x, a, b)
                    self.assertEqual(val | x, x, (a,b,x))
                    self.assertEqual(map_address(val, a, b), val)

    def test_deterministic(self):
        for v in range(0, 65536, 97):
            self.assertEqual(map_address(v, 0, 3), map_address(v, 3, 0))


if __name__ == '__main__': unittest.main()