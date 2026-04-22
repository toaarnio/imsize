from pathlib import Path
import os
import glob
import unittest
import tempfile
import imsize
import numpy as np


thisdir = Path(__file__).parent
imagedir = thisdir / "images"


class ReadTest(unittest.TestCase):

    def test_guess_dims(self):
        for dims in [[1024, 768], [1024, 766], [1920, 1080],
                     [4096, 6144], [4032, 3000], [4032, 6000]]:
            w, h = dims
            width, height = imsize.guess_dims(np.prod(dims))
            self.assertEqual([width, height], [w, h])
        self.assertEqual(imsize.guess_dims(511, min_dim=1), None)

    def _test_guess_packing(self):
        is_packed, bpp = imsize.guess_packing(imagedir / "packed-10bit-3648x2736.raw")
        self.assertTrue(is_packed)
        self.assertEqual(bpp, 10)

    def _test_raw(self):
        info = imsize.read(imagedir / "packed-10bit-3648x2736.raw")
        self.assertEqual(info.filetype, "raw")
        self.assertEqual(info.nchan, 1)
        self.assertEqual(info.width, 3648)
        self.assertEqual(info.height, 2736)
        self.assertEqual(info.bitdepth, 10)
        self.assertEqual(info.bytedepth, 1.25)
        self.assertEqual(info.maxval, 1023)
        self.assertEqual(info.cfa_raw, True)
        self.assertEqual(info.packed_raw, True)
        self.assertEqual(info.isfloat, False)
        self.assertEqual(info.uncertain, True)
        self.assertEqual(info.nbytes, 3648 * 2736 * 10 // 8)

    def test_png(self):
        pngs = glob.glob(os.path.join(imagedir, "*.png"))
        self.assertTrue(len(pngs) > 0)
        for i, png in enumerate(sorted(pngs)):
            info = imsize.read(Path(png))
            self.assertEqual(info.filetype, "png")
            self.assertEqual(info.nchan, 3)
            self.assertTrue(info.width in [600, 450])
            self.assertTrue(info.height in [600, 450])
            self.assertEqual(info.bitdepth, 8)
            self.assertEqual(info.bytedepth, 1)
            self.assertEqual(info.maxval, 255)
            self.assertEqual(info.isfloat, False)
            self.assertEqual(info.uncertain, False)
            self.assertEqual(info.cfa_raw, False)
            self.assertEqual(info.packed_raw, False)
            self.assertEqual(info.nbytes, 600 * 450 * 3)
            self.assertEqual(info.orientation, 0)

    def test_bmp(self):
        bmps = glob.glob(os.path.join(imagedir, "*.bmp"))
        self.assertTrue(len(bmps) > 0)
        for i, bmp in enumerate(sorted(bmps)):
            info = imsize.read(Path(bmp))
            self.assertEqual(info.filetype, "bmp")
            self.assertEqual(info.nchan, 3)
            self.assertTrue(info.width, 640)
            self.assertTrue(info.height, 426)
            self.assertEqual(info.bitdepth, 8)
            self.assertEqual(info.bytedepth, 1)
            self.assertEqual(info.maxval, 255)
            self.assertEqual(info.isfloat, False)
            self.assertEqual(info.uncertain, False)
            self.assertEqual(info.cfa_raw, False)
            self.assertEqual(info.packed_raw, False)
            self.assertEqual(info.nbytes, 640 * 426 * 3)
            self.assertEqual(info.orientation, 0)

    def test_cr2(self):
        cr2s = glob.glob(os.path.join(imagedir, "RAW_CANON_1000D.CR2"))
        self.assertTrue(len(cr2s) >= 0)
        for i, cr2 in enumerate(sorted(cr2s)):
            info = imsize.read(Path(cr2))
            self.assertEqual(info.filetype, "cr2")
            self.assertEqual(info.nchan, 1)
            self.assertEqual(info.width, 3888)
            self.assertEqual(info.height, 2592)
            self.assertEqual(info.bitdepth, 14)
            self.assertEqual(info.bytedepth, 2)
            self.assertEqual(info.maxval, 16383)
            self.assertEqual(info.isfloat, False)
            self.assertEqual(info.uncertain, True)
            self.assertEqual(info.cfa_raw, True)
            self.assertEqual(info.packed_raw, False)
            self.assertEqual(info.nbytes, info.width * info.height * info.bytedepth)
            self.assertEqual(info.orientation, 8)

    def test_exr(self):
        exrs = glob.glob(os.path.join(imagedir, "*.exr"))
        self.assertTrue(len(exrs) > 0)
        for i, exr in enumerate(sorted(exrs)):
            info = imsize.read(Path(exr))
            self.assertEqual(info.filetype, "exr")
            self.assertEqual(info.isfloat, True)
            self.assertEqual(info.cfa_raw, False)
            self.assertEqual(info.packed_raw, False)
            self.assertEqual(info.width, 800)
            self.assertEqual(info.height, 800)
            self.assertEqual(info.nchan, 1)
            self.assertEqual(info.bitdepth, 16)
            self.assertEqual(info.bytedepth, 2)

    def test_npy(self):
        npys = glob.glob(os.path.join(imagedir, "*.npy"))
        self.assertTrue(len(npys) > 0)
        for i, npy in enumerate(sorted(npys)):
            info = imsize.read(Path(npy))
            self.assertEqual(info.filetype, "npy")
            self.assertEqual(info.isfloat, "float" in npy)
            self.assertEqual(info.width, 20)
            self.assertEqual(info.height, 10)
            self.assertEqual(info.nchan, 5)
            self.assertEqual(info.bitdepth, 16)
            self.assertEqual(info.bytedepth, 2)
            self.assertEqual(info.nbytes, 20 * 10 * 5 * 2)

    def test_hdr(self):
        hdrs = glob.glob(os.path.join(imagedir, "*.hdr"))
        self.assertTrue(len(hdrs) > 0)
        for i, hdr in enumerate(sorted(hdrs)):
            info = imsize.read(Path(hdr))
            self.assertEqual(info.filetype, "hdr")
            self.assertEqual(info.isfloat, True)
            self.assertEqual(info.width, 720)
            self.assertEqual(info.height, 480)
            self.assertEqual(info.nchan, 3)
            self.assertEqual(info.bitdepth, 32)
            self.assertEqual(info.bytedepth, 4)
            self.assertEqual(info.nbytes, info.width * info.height * info.nchan * info.bytedepth)

    def test_orientations(self):
        jpegs = sorted(glob.glob(os.path.join(imagedir, "orientations", "*.jpg")))
        tiffs = sorted(glob.glob(os.path.join(imagedir, "orientations", "*.tif")))
        self.assertTrue(len(jpegs) == 16)
        self.assertTrue(len(tiffs) == 16)
        for fmt, fileset in zip(["jpeg", "tiff"], [jpegs, tiffs]):
            for i, filespec in enumerate(fileset):
                info = imsize.read(Path(filespec))
                self.assertEqual(info.filetype, fmt)
                self.assertEqual(info.nchan, 3)
                self.assertTrue(info.width in [600, 450])
                self.assertTrue(info.height in [600, 450])
                self.assertEqual(info.bitdepth, 8)
                self.assertEqual(info.bytedepth, 1)
                self.assertEqual(info.maxval, 255)
                self.assertEqual(info.isfloat, False)
                self.assertEqual(info.uncertain, False)
                self.assertEqual(info.cfa_raw, False)
                self.assertEqual(info.packed_raw, False)
                self.assertEqual(info.nbytes, 600 * 450 * 3)
                self.assertEqual(info.orientation, (i % 8) + 1)

    def test_guess_packing_mipi10(self):
        raw10s = glob.glob(os.path.join(imagedir, "*raw10.mipi"))
        self.assertTrue(len(raw10s) > 0)
        for filespec in sorted(raw10s):
            is_packed, bpp, is_mipi = imsize.guess_packing(Path(filespec))
            self.assertTrue(is_packed)
            self.assertEqual(bpp, 10)
            self.assertTrue(is_mipi)

    def test_guess_packing_mipi12(self):
        raw12s = glob.glob(os.path.join(imagedir, "*raw12.mipi"))
        self.assertTrue(len(raw12s) > 0)
        for filespec in sorted(raw12s):
            is_packed, bpp, is_mipi = imsize.guess_packing(Path(filespec))
            self.assertTrue(is_packed)
            self.assertEqual(bpp, 12)
            self.assertTrue(is_mipi)

    def test_guess_packing_plain10(self):
        plain10s = glob.glob(os.path.join(imagedir, "*plain10.raw"))
        self.assertTrue(len(plain10s) > 0)
        for filespec in sorted(plain10s):
            is_packed, bpp, is_mipi = imsize.guess_packing(Path(filespec))
            self.assertTrue(is_packed)
            self.assertEqual(bpp, 10)
            self.assertFalse(is_mipi)

    def test_guess_packing_plain12(self):
        plain12s = glob.glob(os.path.join(imagedir, "*plain12.raw"))
        self.assertTrue(len(plain12s) > 0)
        for filespec in sorted(plain12s):
            is_packed, bpp, is_mipi = imsize.guess_packing(Path(filespec))
            self.assertTrue(is_packed)
            self.assertEqual(bpp, 12)
            self.assertFalse(is_mipi)

    def test_raw10(self):
        raw10s = glob.glob(os.path.join(imagedir, "*raw10.mipi"))
        self.assertTrue(len(raw10s) > 0)
        for raw10 in sorted(raw10s):
            info = imsize.read(Path(raw10))
            self.assertEqual(info.filetype, "mipi")
            self.assertEqual(info.nchan, 1)
            self.assertEqual(info.width, 640)
            self.assertEqual(info.height, 480)
            self.assertEqual(info.bitdepth, 10)
            self.assertEqual(info.bytedepth, 1.25)
            self.assertEqual(info.maxval, 1023)
            self.assertEqual(info.cfa_raw, True)
            self.assertEqual(info.packed_raw, True)
            self.assertEqual(info.mipi_raw, True)
            self.assertEqual(info.isfloat, False)
            self.assertEqual(info.uncertain, True)
            self.assertEqual(info.nbytes, 640 * 480 * 10 // 8)

    def test_raw12(self):
        raw12s = glob.glob(os.path.join(imagedir, "*raw12.mipi"))
        self.assertTrue(len(raw12s) > 0)
        for raw12 in sorted(raw12s):
            info = imsize.read(Path(raw12))
            self.assertEqual(info.filetype, "mipi")
            self.assertEqual(info.nchan, 1)
            self.assertEqual(info.width, 640)
            self.assertEqual(info.height, 480)
            self.assertEqual(info.bitdepth, 12)
            self.assertEqual(info.bytedepth, 1.5)
            self.assertEqual(info.maxval, 4095)
            self.assertEqual(info.cfa_raw, True)
            self.assertEqual(info.packed_raw, True)
            self.assertEqual(info.mipi_raw, True)
            self.assertEqual(info.isfloat, False)
            self.assertEqual(info.uncertain, True)
            self.assertEqual(info.nbytes, 640 * 480 * 12 // 8)

    def test_empty_files(self):
        for ext in imsize.FILETYPES:
            with tempfile.NamedTemporaryFile(suffix=ext) as fp:
                with self.assertRaises(imsize.ImageFileError):
                    info = imsize.read(fp.name)


if __name__ == "__main__":
    unittest.main()
