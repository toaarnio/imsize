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
            self.assertEqual(info.orientation, 1)

    def test_dng(self):
        dngs = glob.glob(os.path.join(imagedir, "*.dng"))
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
            self.assertEqual(info.orientation, 1)

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
