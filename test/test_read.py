import os
import glob
import unittest
import imsize


thisdir = os.path.dirname(__file__)
imagedir = os.path.join(thisdir, "images")


class ReadTest(unittest.TestCase):

    def test_png(self):
        pngs = glob.glob(os.path.join(imagedir, "*.png"))
        self.assertTrue(len(pngs) > 0)
        for i, png in enumerate(sorted(pngs)):
            info = imsize.read(png)
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
            self.assertEqual(info.nbytes, 600 * 450 * 3)
            self.assertEqual(info.orientation, 0)

    def test_bmp(self):
        bmps = glob.glob(os.path.join(imagedir, "*.bmp"))
        self.assertTrue(len(bmps) > 0)
        for i, bmp in enumerate(sorted(bmps)):
            info = imsize.read(bmp)
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
            self.assertEqual(info.nbytes, 640 * 426 * 3)
            self.assertEqual(info.orientation, 0)

    def test_dng(self):
        dngs = glob.glob(os.path.join(imagedir, "*.DNG"))
        self.assertTrue(len(dngs) > 0)
        for i, dng in enumerate(sorted(dngs)):
            info = imsize.read(dng)
            self.assertEqual(info.filetype, "dng")
            self.assertEqual(info.nchan, 1)
            self.assertTrue(info.width, 7296)
            self.assertTrue(info.height, 3648)
            self.assertEqual(info.bitdepth, 12)
            self.assertEqual(info.bytedepth, 2)
            self.assertEqual(info.maxval, 4095)
            self.assertEqual(info.isfloat, False)
            self.assertEqual(info.uncertain, False)
            self.assertEqual(info.cfa_raw, True)
            self.assertEqual(info.nbytes, 7296 * 3648 * 2)
            self.assertEqual(info.orientation, 0)

    def test_exr(self):
        exrs = glob.glob(os.path.join(imagedir, "*.exr"))
        self.assertTrue(len(exrs) > 0)
        for i, exr in enumerate(sorted(exrs)):
            info = imsize.read(exr)
            self.assertEqual(info.filetype, "exr")
            self.assertEqual(info.isfloat, True)
            self.assertEqual(info.cfa_raw, False)
            self.assertEqual(info.width, 800)
            self.assertEqual(info.height, 800)
            self.assertEqual(info.nchan, 1)
            self.assertEqual(info.bitdepth, 16)
            self.assertEqual(info.bytedepth, 2)

    def test_npy(self):
        npys = glob.glob(os.path.join(imagedir, "*.npy"))
        self.assertTrue(len(npys) > 0)
        for i, npy in enumerate(sorted(npys)):
            info = imsize.read(npy)
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
            info = imsize.read(hdr)
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
                info = imsize.read(filespec)
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
                self.assertEqual(info.nbytes, 600 * 450 * 3)
                self.assertEqual(info.orientation, (i % 8) + 1)


if __name__ == "__main__":
    unittest.main()
