import unittest

from romforge.utils.nes_metasprite import scan_metasprite_candidates


class MetaSpriteScannerTests(unittest.TestCase):
    def test_detects_terminated_oam_like_table(self):
        prg = bytes([
            16, 1, 0x00, 24,
            16, 2, 0x40, 32,
            24, 3, 0x80, 24,
            0xFF,
        ])
        found = scan_metasprite_candidates(prg)
        self.assertEqual(len(found), 1)
        candidate = found[0]
        self.assertEqual(candidate.offset, 0)
        self.assertEqual(candidate.sprite_count, 3)
        self.assertEqual(candidate.width, 16)
        self.assertEqual(candidate.height, 16)

    def test_rejects_reserved_attribute_bits(self):
        prg = bytes([
            16, 1, 0x04, 24,
            16, 2, 0x00, 32,
            24, 3, 0x00, 24,
            0xFF,
        ])
        self.assertEqual(scan_metasprite_candidates(prg), [])

    def test_does_not_duplicate_records_inside_same_table(self):
        prg = bytes([
            8, 1, 0x00, 8,
            8, 2, 0x00, 16,
            16, 3, 0x00, 8,
            16, 4, 0x00, 16,
            0xFF,
        ])
        found = scan_metasprite_candidates(prg)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].sprite_count, 4)


if __name__ == "__main__":
    unittest.main()
