import pathlib
import struct
import tempfile
import unittest

from rebuild.tools.aout_pack import build_exec_header, write_zmagic_image


class AoutPackTest(unittest.TestCase):
    def test_build_exec_header_emits_linux_012_zmagic(self) -> None:
        header = build_exec_header(text_size=64, data_size=16, bss_size=8, entry=0)
        fields = struct.unpack("<8I", header)

        self.assertEqual(0o413, fields[0])
        self.assertEqual(64, fields[1])
        self.assertEqual(16, fields[2])
        self.assertEqual(8, fields[3])
        self.assertEqual(0, fields[5])

    def test_write_zmagic_image_places_text_at_offset_1024(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            output = pathlib.Path(tempdir) / "ls"
            write_zmagic_image(output, text=b"TEXT", data=b"DATA", bss_size=12, entry=0)
            blob = output.read_bytes()

        self.assertEqual(1024, blob.find(b"TEXT"))
        self.assertEqual(b"DATA", blob[1028:1032])


if __name__ == "__main__":
    unittest.main()
