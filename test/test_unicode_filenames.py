import os
from PIL import Image
import numpy as np
import unittest

import imsize
from imsize import ImageFileError

# --- Configuration ---
UNICODE_CHAR = "Ǜ"
TEST_FILENAME_BASE = f"my{UNICODE_CHAR}file"
IMAGE_SIZE = (100, 100) # width, height
IMAGE_COLOR = 'red'

# --- Helper functions for creating dummy files ---

def create_dummy_png(filename):
    img = Image.new('RGB', IMAGE_SIZE, color=IMAGE_COLOR)
    img.save(filename, "png")

def create_dummy_jpeg(filename):
    img = Image.new('RGB', IMAGE_SIZE, color=IMAGE_COLOR)
    img.save(filename, "jpeg")

def create_dummy_bmp(filename):
    img = Image.new('RGB', IMAGE_SIZE, color=IMAGE_COLOR)
    img.save(filename, "bmp")

def create_dummy_tiff(filename):
    img = Image.new('RGB', IMAGE_SIZE, color=IMAGE_COLOR)
    img.save(filename, "tiff")

def create_dummy_pnm(filename):
    width, height = IMAGE_SIZE
    pixels = np.zeros((height, width, 3), dtype=np.uint8)
    pixels[:,:] = [255, 0, 0] # Red
    with open(filename, 'wb') as f:
        f.write(b"P6\n")
        f.write(f"{width} {height}\n".encode('ascii'))
        f.write(b"255\n")
        f.write(pixels.tobytes())

def create_dummy_pfm(filename):
    width, height = IMAGE_SIZE
    pixels = np.zeros((height, width, 3), dtype=np.float32)
    pixels[:,:] = [1.0, 0.0, 0.0] # Red
    with open(filename, 'wb') as f:
        f.write(b"PF\n") # Color PFM
        f.write(f"{width} {height}\n".encode('ascii'))
        f.write(b"-1.0\n") # Little-endian
        pixels.tofile(f)

def create_dummy_hdr(filename):
    width, height = IMAGE_SIZE
    with open(filename, 'wb') as f:
        f.write(b"#?RADIANCE\n")
        f.write(b"# Made with imsize test suite\n")
        f.write(b"FORMAT=32-bit_rle_rgbe\n")
        f.write(b"\n")
        f.write(f"-Y {height} +X {width}\n".encode('ascii'))
        f.write(b'\x02\x02\x02\x02') # RGBE for one pixel

def create_dummy_exr(filename):
    raise NotImplementedError("Creating dummy EXR files programmatically is complex and requires specialized libraries.")

def create_dummy_npy(filename):
    width, height = IMAGE_SIZE
    arr = np.zeros((height, width, 3), dtype=np.uint8)
    arr[:,:] = [255, 0, 0] # Red
    np.save(filename, arr)

def create_dummy_raw(filename):
    width, height = IMAGE_SIZE
    data = np.zeros((height, width), dtype=np.uint16)
    data[::2, ::2] = 1000
    data[1::2, 1::2] = 2000
    data.tofile(filename)

def create_dummy_empty_file(filename):
    with open(filename, 'w') as f:
        f.write("")

# Map file extensions to their creation functions
FILE_CREATORS = {
    ".png": create_dummy_png,
    ".pnm": create_dummy_pnm,
    ".pgm": create_dummy_pnm,
    ".ppm": create_dummy_pnm,
    ".pfm": create_dummy_pfm,
    ".bmp": create_dummy_bmp,
    ".jpeg": create_dummy_jpeg,
    ".jpg": create_dummy_jpeg,
    ".insp": create_dummy_jpeg,
    ".tiff": create_dummy_tiff,
    ".tif": create_dummy_tiff,
    ".exr": create_dummy_exr,
    ".hdr": create_dummy_hdr,
    ".dng": create_dummy_empty_file,
    ".cr2": create_dummy_empty_file,
    ".nef": create_dummy_empty_file,
    ".raw": create_dummy_raw,
    ".npy": create_dummy_npy,
}

# Supported file extensions from imsize.py
ALL_SUPPORTED_FILETYPES = [".png", ".pnm", ".pgm", ".ppm", ".pfm", ".bmp",
                           ".jpeg", ".jpg", ".insp", ".tiff", ".tif",
                           ".exr", ".hdr", ".dng", ".cr2", ".nef", ".raw", ".npy"]

class TestUnicodeFilenames(unittest.TestCase):
    def setUp(self):
        self.created_files = []

    def tearDown(self):
        for f in self.created_files:
            if os.path.exists(f):
                os.remove(f)

    def _run_unicode_test_for_format(self, ext):
        unicode_filename = f"{TEST_FILENAME_BASE}{ext}"
        self.created_files.append(unicode_filename)

        creator_func = FILE_CREATORS.get(ext)
        self.assertIsNotNone(creator_func, f"No creator function defined for {ext}")

        try:
            creator_func(unicode_filename)
        except NotImplementedError:
            self.skipTest(f"Skipping {ext}: Creating dummy EXR files is complex.")

        # Test reading with imsize.read()
        if ext in [".dng", ".cr2", ".nef", ".raw"]:
            # For formats where we expect ImageFileError due to empty content
            with self.assertRaises(ImageFileError) as cm:
                imsize.read(unicode_filename)
            self.assertIn("not a recognized", str(cm.exception), f"Expected 'not a recognized' error for {ext}")
        else:
            info = imsize.read(unicode_filename)
            self.assertEqual(info.filespec, unicode_filename, f"Filespec mismatch for {ext}")
            self.assertTrue(info.width is not None or info.uncertain, f"Width not extracted for {ext}")
            self.assertTrue(info.height is not None or info.uncertain, f"Height not extracted for {ext}")

    def test_png_unicode_filename(self):
        self._run_unicode_test_for_format(".png")

    def test_pnm_unicode_filename(self):
        self._run_unicode_test_for_format(".pnm")

    def test_pgm_unicode_filename(self):
        self._run_unicode_test_for_format(".pgm")

    def test_ppm_unicode_filename(self):
        self._run_unicode_test_for_format(".ppm")

    def test_pfm_unicode_filename(self):
        self._run_unicode_test_for_format(".pfm")

    def test_bmp_unicode_filename(self):
        self._run_unicode_test_for_format(".bmp")

    def test_jpeg_unicode_filename(self):
        self._run_unicode_test_for_format(".jpeg")

    def test_jpg_unicode_filename(self):
        self._run_unicode_test_for_format(".jpg")

    def test_insp_unicode_filename(self):
        self._run_unicode_test_for_format(".insp")

    def test_tiff_unicode_filename(self):
        self._run_unicode_test_for_format(".tiff")

    def test_tif_unicode_filename(self):
        self._run_unicode_test_for_format(".tif")

    def test_exr_unicode_filename(self):
        self._run_unicode_test_for_format(".exr")

    def test_hdr_unicode_filename(self):
        self._run_unicode_test_for_format(".hdr")

    def test_dng_unicode_filename(self):
        self._run_unicode_test_for_format(".dng")

    def test_cr2_unicode_filename(self):
        self._run_unicode_test_for_format(".cr2")

    def test_nef_unicode_filename(self):
        self._run_unicode_test_for_format(".nef")

    def test_raw_unicode_filename(self):
        self._run_unicode_test_for_format(".raw")

    def test_npy_unicode_filename(self):
        self._run_unicode_test_for_format(".npy")


if __name__ == '__main__':
    unittest.main()
