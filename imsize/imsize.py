"""
Extracts image dimensions, bit depth, and other basic metadata.

Example:
  info = imsize.read("myfile.jpg")
  factor = info.nbytes / info.filesize
  print(f"{info.filespec}: compression factor = {factor.1f}")

https://github.com/toaarnio/imsize
"""
from __future__ import annotations

import os              # built-in library
import sys             # built-in library
import math            # built-in library
import struct          # built-in library
import ast             # built-in library
import pprint          # built-in library
import contextlib      # built-in library
import sympy           # pip install sympy
import pyexiv2         # pip install pyexiv2
import exiftool        # pip install pyexiftool
import rawpy           # pip install rawpy
import numpy as np     # pip install numpy

try:
    # package mode
    from imsize import pnmhdr   # local import: pnmhdr.py
    from imsize import pfmhdr   # local import: pfmhdr.py
    from imsize import exrhdr   # local import: exrhdr.py
except ImportError:
    # stand-alone mode
    import pnmhdr
    import pfmhdr
    import exrhdr


######################################################################################
#
#  P U B L I C   A P I
#
######################################################################################


FILETYPES = [".png", ".pnm", ".pgm",
             ".ppm", ".pfm", ".bmp",
             ".jpeg", ".jpg", ".insp",
             ".tiff", ".tif", ".exr",
             ".hdr", ".dng", ".cr2",
             ".nef", ".raw", ".mipi",
             ".npy"]


class ImageInfo:
    """
    A container for image metadata, filled in and returned by read().

    Attributes:
      filespec (str): The filespec given to read(), copied verbatim
      filetype (str): File type: png|pnm|pfm|bmp|jpeg|insp|tiff|exr|hdr|dng|cr2|nef|raw|mipi|npy|...
      filesize (int): Size of the file on disk in bytes
      multi_picture (bool): True if there is more than one image in the file
      num_images (int): Number of images contained in the file
      image_sizes (list): Size of each image in the file, in bytes
      image_offsets (list): Offset of each image in the file, in bytes
      header_size (int): Size of .raw file header in bytes
      isfloat (bool): True if the image is in floating-point format
      cfa_raw (bool): True if the image is in CFA (Bayer) raw format
      packed_raw (bool): True if the image is in any bit-packed raw format
      mipi_raw (bool): True if the image is in MIPI bit-packed raw format
      npixels (int): Size of the image in pixels (width & height may be unknown)
      width (int): Width of the image in pixels (orientation ignored)
      height (int): Height of the image in pixels (orientation ignored)
      stride (int): Width of the image in bytes
      nchan (int): Number of color channels: 1, 2, 3 or 4
      bitdepth (int): Bits per sample: 1 to 32
      bytedepth (float): Bytes per sample; may be fractional if packed_raw is True
      maxval (int): Maximum representable sample value, e.g., 255
      nbytes (int): Size of the image in bytes, uncompressed
      orientation (int): Image orientation in EXIF format: 1 to 8, or 0 (unknown)
      rot90_ccw_steps (int): Number of rotations to bring the image upright: 0 to 3
      uncertain (bool): True if width/height/bitdepth are uncertain
    """
    def __init__(self):
        self.filespec = None
        self.filetype = None
        self.filesize = None
        self.multi_picture = None
        self.num_images = None
        self.image_sizes = None
        self.image_offsets = None
        self.header_size = None
        self.isfloat = None
        self.cfa_raw = None
        self.packed_raw = None
        self.mipi_raw = None
        self.npixels = None
        self.width = None
        self.height = None
        self.stride = None
        self.nchan = None
        self.bitdepth = None
        self.bytedepth = None
        self.maxval = None
        self.nbytes = None
        self.orientation = None
        self.rot90_ccw_steps = None
        self.uncertain = None

    def __repr__(self):
        reprstr = f"<ImageInfo {self.__dict__}>"
        return reprstr

    def __str__(self):
        infostr = pprint.pformat(self.__dict__, sort_dicts=False)
        return infostr


def read(filespec: str) -> ImageInfo:
    """
    Parses a lowest common denominator set of metadata from the given
    image, i.e., the dimensions and bit depth. Does not read the entire
    file but only what's necessary. If the file type is recognized and
    parsing succeeds, returns an ImageInfo with all fields filled in.
    Otherwise, an exception is raised or only the basic file attributes
    (name, type, size) are filled in.

    Example:
      info = imsize.read("myfile.jpg")
      factor = info.nbytes / info.filesize
      print(f"{info.filespec}: compression factor = {factor.1f}")
    """
    filename = os.path.basename(filespec)             # "path/image.ext" => "image.ext"
    extension = os.path.splitext(filename)[-1]        # "image.ext" => ".ext"
    filetype = extension.lower()[1:]                  # ".EXT" => "ext"
    handlers = {"png": _read_png,
                "pnm": _read_pnm,
                "pgm": _read_pnm,
                "ppm": _read_pnm,
                "pfm": _read_pfm,
                "bmp": _read_bmp,
                "jpeg": _read_jpeg,
                "jpg": _read_jpeg,
                "insp": _read_insp,
                "tiff": _read_tiff,
                "tif": _read_tiff,
                "exr": _read_exr,
                "hdr": _read_hdr,
                "dng": _read_dng,
                "cr2": _read_cr2,
                "nef": _read_nef,
                "raw": _read_raw,
                "mipi": _read_mipi,
                "npy": _read_npy}

    # Check that we have a parser for each known filetype, and
    # conversely, that all filetypes are listed for which we have
    # a parser

    filetypes = {ext[1:] for ext in FILETYPES}  # .ext => ext
    assert set(handlers) == filetypes, set(handlers) ^ filetypes

    if filetype in handlers:
        handler = handlers[filetype]
        try:
            info = handler(filespec)
        except ImageFileError:
            raise
        except Exception as e:
            raise ImageFileError(f"File {filespec} is not a recognized {filetype.upper()} file.") from e
        else:
            return info
    else:
        # unrecognized file extension
        info = ImageInfo()
        info.filespec = filespec
        info.filetype = filetype
        info.filesize = os.path.getsize(filespec)
        info.nbytes = info.filesize
        info.uncertain = True
        return info


def guess_packing(filespec: str) -> tuple[bool, int, bool | None]:
    """
    Try to guess whether a raw file is unpacked (2 bytes per pixel),
    12-bit packed (3 bytes per 2 pixels), or 10-bit packed (5 bytes
    per 4 pixels). For packed files, also distinguish MIPI packing
    from plain/SMIA packing using a pedestal-based test.

    The pedestal test decodes the sample with both candidate decoders
    and checks which one yields a 2nd-percentile value above the lower
    tail of an assumed dark noise distribution (40 DN for 10-bit).
    Erroneously decoded samples would be expected to have a greater
    percentage of near-zero values.

    Note the following assumptions and limitations:
    1. Only 10-bit and 12-bit formats are recognized;
    2. Dark 12-bit unpacked images may be categorized as 10-bit;
    3. Headers and footers may adversely affect reliability;
    4. Unpacked images are assumed to be little-endian (x86);
    5. The analysis is based on the first 150 kB of the file;
    6. Extremely noisy images may be miscategorized.

    :param filespec: raw file to analyze
    :returns is_packed: True if the raw data is bit-packed
    :returns bpp: bits per pixel, can be either 10 or 12
    :returns is_mipi: True=MIPI, False=unpacked/other, None=ambiguous
    """
    def get_periodicity_score(p):
        cols = data.reshape(-1, p)
        col_stds = np.std(cols, axis=0)
        score = np.std(col_stds) / (np.mean(col_stds) + 1e-6)
        return score

    def p02(pixels):
        return int(np.percentile(pixels, 2.0))

    def decode_plain10(raw):
        # LSB-first contiguous packing of 4 x 10-bit pixels into 5 bytes:
        #   byte0: a7 a6 a5 a4 a3 a2 a1 a0
        #   byte1: b5 b4 b3 b2 b1 b0 a9 a8
        #   byte2: c3 c2 c1 c0 b9 b8 b7 b6
        #   byte3: d1 d0 c9 c8 c7 c6 c5 c4
        #   byte4: d9 d8 d7 d6 d5 d4 d3 d2
        b = raw[:len(raw) - len(raw) % 5].reshape(-1, 5)
        p = np.empty((len(b), 4), dtype=np.uint16)
        p[:, 0] = b[:, 0].astype(np.uint16) | ((b[:, 1].astype(np.uint16) & 0x03) << 8)
        p[:, 1] = (b[:, 1].astype(np.uint16) >> 2) | ((b[:, 2].astype(np.uint16) & 0x0F) << 6)
        p[:, 2] = (b[:, 2].astype(np.uint16) >> 4) | ((b[:, 3].astype(np.uint16) & 0x3F) << 4)
        p[:, 3] = (b[:, 3].astype(np.uint16) >> 6) | (b[:, 4].astype(np.uint16) << 2)
        return p.flatten()

    def decode_plain12(raw):
        # LSB-first contiguous packing of 2 x 12-bit pixels into 3 bytes:
        #   byte0: a7 a6 a5 a4 a3 a2 a1 a0
        #   byte1: b3 b2 b1 b0 aB aA a9 a8
        #   byte2: cB cA c9 c8 b7 b6 b5 b4
        b = raw[:len(raw) - len(raw) % 3].reshape(-1, 3)
        p = np.empty((len(b), 2), dtype=np.uint16)
        p[:, 0] = b[:, 0].astype(np.uint16) | ((b[:, 1].astype(np.uint16) & 0x0F) << 8)
        p[:, 1] = (b[:, 1].astype(np.uint16) >> 4) | (b[:, 2].astype(np.uint16) << 4)
        return p.flatten()

    def decode_mipi10(raw):
        # MSB-first disjoint packing of 4 x 10-bit pixels into 5 bytes:
        #   byte0: a9 a8 a7 a6 a5 a4 a3 a2
        #   byte1: b9 b8 b7 b6 b5 b4 b3 b2
        #   byte2: c9 c8 c7 c6 c5 c4 c3 c2
        #   byte3: d9 d8 d7 d6 d5 d4 d3 d2
        #   byte4: a1 a0 b1 b0 c1 c0 d1 d0
        b = raw[:len(raw) - len(raw) % 5].reshape(-1, 5)
        p = np.empty((len(b), 4), dtype=np.uint16)
        p[:, 0] = (b[:, 0].astype(np.uint16) << 2) | ((b[:, 4] >> 6) & 3)
        p[:, 1] = (b[:, 1].astype(np.uint16) << 2) | ((b[:, 4] >> 4) & 3)
        p[:, 2] = (b[:, 2].astype(np.uint16) << 2) | ((b[:, 4] >> 2) & 3)
        p[:, 3] = (b[:, 3].astype(np.uint16) << 2) | (b[:, 4] & 3)
        return p.flatten()

    def decode_mipi12(raw):
        # MSB-first disjoint packing of 2 x 12-bit pixels into 3 bytes:
        #   byte0: aB aA a9 a8 a7 a6 a5 a4
        #   byte1: bB bB b9 b8 b7 b6 b5 b4
        #   byte2: a3 a2 a1 a0 b3 b2 b1 b0
        b = raw[:len(raw) - len(raw) % 3].reshape(-1, 3)
        p = np.empty((len(b), 2), dtype=np.uint16)
        p[:, 0] = (b[:, 0].astype(np.uint16) << 4) | ((b[:, 2] >> 4) & 0xF)
        p[:, 1] = (b[:, 1].astype(np.uint16) << 4) | (b[:, 2] & 0xF)
        return p.flatten()

    data = np.fromfile(filespec, dtype=np.uint8, count=1024 * 150)
    data = data[3000:]  # should be enough to skip any headers
    scores = {p: get_periodicity_score(p) for p in [2, 3, 5]}
    winner = max(scores, key=scores.get)
    period_to_bpp = {2: 0, 3: 12, 5: 10}
    bpp = period_to_bpp[winner]

    if bpp == 0:  # unpacked
        bpp = guess_bpp(data.view(np.uint16))
        return False, bpp, False

    # Choose a bit-packing format that results in at most 2% of pixels
    # lying below 40 DN at 10 bpp; this assumes a typical pedestal value
    # of 50-70 DN and not an excessive amount of noise in dark regions

    if bpp == 10:
        min_pedestal = 40
        mipi_ok  = p02(decode_mipi10(data)) >= min_pedestal
        plain_ok = p02(decode_plain10(data)) >= min_pedestal
    if bpp == 12:
        min_pedestal = 160
        mipi_ok  = p02(decode_mipi12(data)) >= min_pedestal
        plain_ok = p02(decode_plain12(data)) >= min_pedestal

    if mipi_ok and not plain_ok:
        is_mipi = True
    elif plain_ok and not mipi_ok:
        is_mipi = False
    else:
        is_mipi = None  # ambiguous: both or neither match the pedestal window

    return True, bpp, is_mipi


def guess_bpp(raw: np.ndarray) -> int:
    """
    Try to guess the bit depth of the given unpacked raw data. The data
    is assumed to have no header, footer, or any other non-pixel data.

    :param raw: raw pixel data to analyze; dtype = np.uint16
    :returns: bits per pixel, can be either 10 or 12
    """
    maxx = max(np.max(raw), 1)  # log2(0) would fail
    minbits = np.ceil(np.log2(maxx))  # 5, 6, 7, ..., 16
    minbits = np.ceil(minbits / 2) * 2  # 6, 8, 10, 12, ..., 16
    minbits = np.clip(minbits, 10, 12)  # 10 or 12
    minbits = int(minbits)
    return minbits


def guess_dims(num_pixels: int, min_dim: int = 256) -> list[int, int] | None:
    """
    Try to guess a width and height for the given number of pixels, with
    the following assumptions and rules:

    1. No surplus data, such as headers or footers
    2. width % 4 == 0
    3. height % 2 == 0
    4. 1.5 >= height/width >= 0.4
    5. Aspect ratio probability order: 3/4, 3/2, 2/3, 9/16, 1

    :param num_pixels: number of pixels (not bytes)
    :param min_dim: required minimum height and width
    :returns: most probable width & height, or None
    """
    candidates = sympy.ntheory.divisors(num_pixels)  # 24 => [1, 2, 3, 4, 6, 8, 12, 24]
    candidates = [n for n in candidates if min_dim <= n <= num_pixels // min_dim]
    if candidates:
        pairs = np.asarray(list(zip(candidates, candidates[::-1])))
        aspects = pairs[:, 1] / pairs[:, 0]  # height / width
        valid = (aspects <= 1.5) * (aspects >= 0.4)
        valid *= (pairs[:, 0] % 4 == 0) * (pairs[:, 1] % 2 == 0)
        if np.any(valid):
            pairs = pairs[valid]
            aspects = aspects[valid]
            for atol in [1e-4, 0.02]:  # try exact matches first, then approximate
                for cand in [3/4, 3/2, 2/3, 9/16, 1]:
                    closest = np.argmin(np.abs(aspects - cand))
                    if np.isclose(aspects[closest], cand, atol=atol):
                        dims = pairs[closest].tolist()
                        return dims


class ImageFileError(Exception):
    """
    A custom exception raised in all known error conditions.
    """


######################################################################################
#
#  I N T E R N A L   F U N C T I O N S
#
######################################################################################


@contextlib.contextmanager
def silence_stdout():
    stdout_fd = sys.stdout.fileno()
    orig_fd = os.dup(stdout_fd)
    null_fd = os.open(os.devnull, os.O_WRONLY)
    os.dup2(null_fd, stdout_fd)
    try:
        yield
    finally:
        os.dup2(orig_fd, stdout_fd)
        os.close(orig_fd)
        os.close(null_fd)


def _read_png(filespec):
    info = ImageInfo()
    info.filespec = filespec
    info.filetype = "png"
    info.isfloat = False
    info.cfa_raw = False
    info.packed_raw = False
    with open(filespec, "rb") as f:
        header = f.read(26)
        signature = bytes([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a])
        if header.startswith(signature) and header[12:16] == b"IHDR":
            ihdr = struct.unpack(">LLBB", header[16:26])
            info.width = ihdr[0]
            info.height = ihdr[1]
            info.bitdepth = ihdr[2]
            info.nchan = {0: 1,           # greyscale => 1 channel
                          2: 3,           # truecolor => 3 channels
                          3: 3,           # indexed => 3 channels
                          4: 2,           # greyscale_alpha => 2 channels
                          6: 4}[ihdr[3]]  # truecolor_alpha => 4 channels
            info = _complete(info)
            return info
    raise ImageFileError(f"File {filespec} is not a valid PNG file.")


def _read_pnm(filespec):
    info = ImageInfo()
    shape, maxval = pnmhdr.dims(filespec)
    info.filespec = filespec
    info.filetype = "pnm"
    info.isfloat = False
    info.cfa_raw = False
    info.packed_raw = False
    info.width = shape[1]
    info.height = shape[0]
    info.nchan = 1 if len(shape) < 3 else shape[2]
    info.maxval = maxval
    info = _complete(info)
    return info


def _read_pfm(filespec):
    info = ImageInfo()
    shape, maxval = pfmhdr.dims(filespec)
    info.filespec = filespec
    info.filetype = "pfm"
    info.isfloat = True
    info.cfa_raw = False
    info.packed_raw = False
    info.width = shape[1]
    info.height = shape[0]
    info.nchan = 1 if len(shape) < 3 else shape[2]
    info.maxval = maxval
    info.bitdepth = 32
    info.bytedepth = 4
    info = _complete(info)
    return info


def _read_hdr(filespec):
    info = ImageInfo()
    info.filespec = filespec
    info.filetype = "hdr"
    info.filesize = os.path.getsize(filespec)
    info.isfloat = True
    info.cfa_raw = False
    info.packed_raw = False
    info.nchan = 3
    info.bitdepth = 32
    info.bytedepth = 4
    with open(filespec, "rb") as f:
        if f.readline() != b"#?RADIANCE\n":
            raise ImageFileError(f"File {filespec} is not a valid Radiance HDR file.")
        for line in f:
            if line == b"\n":
                dims = f.readline().decode("utf-8")  # '-Y 480 +X 720'
                dims = dims.split(" ")
                info.height = int(dims[1])
                info.width = int(dims[3])
                info = _complete(info)
                return info
    raise ImageFileError(f"File {filespec} is not a valid Radiance HDR file.")


def _read_bmp(filespec):
    info = ImageInfo()
    info.filespec = filespec
    info.filetype = "bmp"
    info.isfloat = False
    info.cfa_raw = False
    info.packed_raw = False
    with open(filespec, "rb") as f:
        bmp_header = f.read(14)
        if bmp_header[:2] == b"BM":
            dib_header_size = np.fromfile(f, dtype=np.uint32, count=1)
            fmt = "<HHHH" if dib_header_size == 12 else "<iiHH"
            dib_header = struct.unpack(fmt, f.read(struct.calcsize(fmt)))
            info.width = dib_header[0]
            info.height = abs(dib_header[1])  # negative => top to bottom
            bpp = dib_header[3]
            info.nchan = {1: 1,        # 1 bpp => 1 channel
                          2: 3,        # 2 bpp palettized => 3 channels
                          4: 3,        # 4 bpp palettized => 3 channels
                          8: 3,        # 8 bpp palettized => 3 channels
                          16: 4,       # 16 bpp RGBA => 4 channels
                          24: 3,       # 24 bpp RGB => 3 channels
                          32: 4}[bpp]  # 32 bpp RGBA => 4 channels
            info.maxval = 255
            info = _complete(info)
            return info
    raise ImageFileError(f"File {filespec} is not a valid BMP file.")


def _read_exr(filespec):
    info = ImageInfo()
    info.filespec = filespec
    info.filetype = "exr"
    info.cfa_raw = False
    info.packed_raw = False
    info.maxval = 1.0
    w, h, nchan, isfloat, bitdepth = exrhdr.dims(filespec)
    info.width = w
    info.height = h
    info.nchan = nchan
    info.isfloat = isfloat
    info.bitdepth = bitdepth
    info.bytedepth = bitdepth // 8
    info = _complete(info)
    return info


def _read_jpeg(filespec):
    info = _read_exif_pyexiv2(filespec)
    if info is not None:
        info.filespec = filespec
        info.filetype = "jpeg"
        info.isfloat = False
        info.cfa_raw = False
        info.packed_raw = False
        with open(filespec, "rb") as f:
            if f.read(2) == b"\xff\xd8":
                size = 2
                segtype = 0
                while not 0xc0 <= segtype <= 0xcf or segtype in [0xc4, 0xc8, 0xcc]:
                    f.seek(size - 2, 1)  # skip to next segment
                    _0xff, segtype, size = struct.unpack(">BBH", f.read(4))
                    if segtype == 0xe2:  # APP2
                        prev_pos = f.tell()
                        # Detect Multi-Picture Format (MPF) as per CIPA DC-007-2009
                        if f.read(4) == b"MPF\x00":
                            endianness = f.read(4)
                            bo = ">" if endianness == b"MM\x00*" else "<"
                            offset, count = struct.unpack(f"{bo}IH", f.read(6))
                            version_tag, version = struct.unpack(f"{bo}Hxxxxxx4s", f.read(12))
                            nimages_tag, nimages = struct.unpack(f"{bo}HxxxxxxI", f.read(12))
                            mpentry_tag, = struct.unpack(f"{bo}Hxxxxxxxxxx", f.read(12))
                            _next_ifd, = struct.unpack(f"{bo}I", f.read(4))
                            prefix = f"Error parsing MPF JPEG '{filespec}':"
                            assert offset == 8, f"{prefix}: Expected offset 8, got {offset}"
                            assert count == 3, f"{prefix}: Expected count 3, got {count}"
                            assert version_tag == 45056, f"{prefix}: Expected tag id 45056 (MPFVersion), got {version_tag}"
                            assert version == b"0100", f"{prefix}: Expected version '0100', got {version}"
                            assert nimages_tag == 45057, f"{prefix}: Expected tag id 45057 (NumberOfImages), got {nimages_tag}"
                            assert nimages in [2, 3], f"{prefix}: Expected 2 or 3 sub-images, got {nimages}"
                            assert mpentry_tag == 45058, f"{prefix}: Expected tag id 45058 (MPEntry), got {mpentry_tag}"
                            info.multi_picture = True
                            info.num_images = nimages
                            info.image_sizes = []
                            info.image_offsets = []
                            for _ in range(info.num_images):
                                _attrs, imsize, offset, _entry1, _entry2 = struct.unpack(f"{bo}IIIHH", f.read(16))
                                info.image_offsets.append(offset + prev_pos + 4)
                                info.image_sizes.append(imsize)
                        f.seek(prev_pos)
                sof = struct.unpack(">BHHB", f.read(6))
                info.bitdepth = sof[0]
                info.height = sof[1]
                info.width = sof[2]
                info.nchan = sof[3]
                info = _complete(info)
                return info
    raise ImageFileError(f"File {filespec} is not a valid JPEG file.")


def _read_insp(filespec):
    info = _read_jpeg(filespec)
    info.filetype = "insp"
    return info


def _rot90_steps(exif_orientation):
    exif_to_rot90 = {1: 0, 2: 0, 3: 2, 4: 0, 5: 1, 6: 3, 7: 3, 8: 1}
    rot90_ccw_steps = exif_to_rot90.get(exif_orientation)
    return rot90_ccw_steps


def _read_exif_pyexiv2(filespec):
    try:
        with silence_stdout(), pyexiv2.Image(str(filespec)) as img:
            encodings = ["utf-8", "ISO-8859-1"]
            for encoding in encodings:
                try:
                    exif = img.read_exif(encoding)
                except UnicodeDecodeError:
                    continue
        subimages = ["Image", "SubImage1", "SubImage2", "SubImage3"]
        widths = [exif.get(f"Exif.{sub}.ImageWidth") for sub in subimages]
        widths = [int(w or 0) for w in widths]  # None => 0
        maximg = subimages[np.argmax(widths)]  # use the largest sub-image
        info = ImageInfo()
        info.packed_raw = False
        info.cfa_raw = exif.get(f"Exif.{maximg}.PhotometricInterpretation") in ['32803', '34892']
        info.width = int(exif.get(f"Exif.{maximg}.ImageWidth", 0))
        info.height = int(exif.get(f"Exif.{maximg}.ImageLength", 0))
        info.nchan = int(exif.get(f"Exif.{maximg}.SamplesPerPixel", 0))
        info.bitdepth = exif.get(f"Exif.{maximg}.BitsPerSample", "0")
        info.orientation = int(exif.get(f"Exif.{maximg}.Orientation", 0))
        info.rot90_ccw_steps = _rot90_steps(info.orientation)
        if isinstance(info.bitdepth, str):
            bitdepths = tuple(int(el) for el in info.bitdepth.split(" "))  # string => tuple of ints
            info.bitdepth = bitdepths[0]
    except RuntimeError:
        return None
    else:
        return info


def _multikey(meta, *keys):
    value = meta.get(keys[0])
    if value is None and len(keys) > 1:
        return _multikey(meta, *keys[1:])
    return value


def _read_exif_exiftool(filespec):
    with exiftool.ExifToolHelper() as et:
        meta = et.get_metadata(filespec)[0]
        info = ImageInfo()
        info.packed_raw = False
        info.cfa_raw = meta["EXIF:PhotometricInterpretation"] in [32803, 34892]
        info.width = _multikey(meta, "EXIF:ExifImageWidth", "XMP:ImageWidth", "EXIF:ImageWidth")
        info.height = _multikey(meta, "EXIF:ExifImageHeight", "XMP:ImageHeight", "EXIF:ImageHeight")
        info.nchan = meta["EXIF:SamplesPerPixel"]
        info.bitdepth = meta["EXIF:BitsPerSample"]
        info.orientation = meta["EXIF:Orientation"]
        info.rot90_ccw_steps = _rot90_steps(info.orientation)
        if isinstance(info.bitdepth, str):
            bitdepths = tuple(int(el) for el in info.bitdepth.split(" "))  # string => tuple of ints
            info.bitdepth = bitdepths[0]
        return info


def _read_tiff(filespec):
    info = _read_exif_pyexiv2(filespec)
    if info is None:
        info = _read_exif_exiftool(filespec)
    info.filespec = filespec
    info.filetype = "tiff"
    info.isfloat = False
    info = _complete(info)
    return info


def _read_dng(filespec):
    info = _read_exif_pyexiv2(filespec)
    if info is None:
        info = _read_exif_exiftool(filespec)
    info.filespec = filespec
    info.filetype = "dng"
    info.isfloat = False
    info = _complete(info)
    return info


def _read_cr2(filespec):
    info = _read_exif_exiftool(filespec)
    info.filespec = filespec
    info.filetype = "cr2"
    info.uncertain = True
    info.isfloat = False
    info.cfa_raw = True
    info.nchan = 1
    info.bytedepth = 2
    info.bitdepth = 14  # 14-bit since Canon 450D (2008)
    info = _complete(info)
    return info


def _read_nef(filespec):  # reading the whole file ==> SLOW
    raw = rawpy.imread(filespec)
    raw = raw.raw_image_visible
    info = ImageInfo()
    info.filespec = filespec
    info.filetype = "nef"
    info.uncertain = True
    info.isfloat = False
    info.cfa_raw = True
    info.nchan = 1
    info.bytedepth = 2
    info.height, info.width = raw.shape
    minbits = np.ceil(np.log2(np.max(raw)))  # 5, 6, 7, ..., 16
    minbits = np.ceil(minbits / 2) * 2  # 6, 8, 10, 12, ..., 16
    minbits = max(minbits, 12)  # 12, 14, 16
    info.bitdepth = int(minbits)  # can underestimate bpp if image is very dark
    info = _complete(info)
    return info


def _guess_raw_dims(info):
    """
    Fills in info.width, info.height, and info.header_size by guessing from
    info.npixels (already set by the caller). First tries exact divisor-based
    matching via guess_dims(); if that fails, falls back to aspect-ratio
    heuristics that tolerate a small header/footer.

    :param info: ImageInfo with npixels, filesize, and bytedepth already set
    :returns: the same info object, with width/height/header_size updated
    """
    dims = guess_dims(info.npixels)
    if dims is not None:  # exact match, no surplus bytes
        info.width, info.height = dims
        return info
    for aspect in [3/4, 2/3, 9/16]:  # try typical aspect ratios
        h = math.sqrt(info.npixels * aspect)
        w = info.npixels / h
        wrem4 = w % 4
        hrem4 = h % 4
        if wrem4 == 0 and hrem4 == 0:
            info.width, info.height = int(w), int(h)
            break
        if wrem4 < 0.5 and hrem4 < 0.5:
            info.width, info.height = int(w), int(h)
            info.header_size = info.filesize - info.width * info.height * info.bytedepth
            break
    return info


def _read_raw(filespec):
    info = ImageInfo()
    info.filespec = filespec
    info.filetype = "raw"
    info.uncertain = True  # width, height & bitdepth are guessed
    info.isfloat = False
    info.cfa_raw = True
    info.nchan = 1
    info.header_size = 0  # assume no header
    info.filesize = os.path.getsize(filespec)
    assert info.filesize > 256 * 256 * 2, f"{filespec} is too small ({info.filesize} bytes) to be a valid camera raw file."
    info.packed_raw, info.bitdepth, info.mipi_raw = guess_packing(filespec)
    info.bytedepth = (info.bitdepth / 8) if info.packed_raw else 2
    info.nbytes = info.filesize
    info.npixels = int(info.filesize / info.bytedepth)
    info = _guess_raw_dims(info)
    info = _complete(info)
    return info


def _read_mipi(filespec):
    """
    Reads MIPI RAW10 or RAW12 bit-packed camera raw files. In MIPI RAW10,
    four 10-bit pixels are packed into five bytes. In MIPI RAW12, two 12-bit
    pixels are packed into three bytes. Width and height are guessed from the
    file size.
    """
    info = ImageInfo()
    info.filespec = filespec
    info.filetype = "mipi"
    info.mipi_raw = True  # we only get here if the suffix is .mipi
    info.packed_raw = True  # MIPI raw files are always packed
    info.uncertain = True  # width, height & bitdepth are guessed
    info.isfloat = False
    info.cfa_raw = True
    info.nchan = 1
    info.header_size = 0  # MIPI raw files have no header
    info.filesize = os.path.getsize(filespec)
    assert info.filesize > 256 * 256 * 2, f"{filespec} is too small ({info.filesize} bytes) to be a valid MIPI raw file."
    info.bitdepth = guess_packing(filespec)[1]
    info.bytedepth = (info.bitdepth / 8) if info.packed_raw else 2
    info.npixels = int(info.filesize / info.bytedepth)
    info.nbytes = info.filesize
    info = _guess_raw_dims(info)
    info = _complete(info)
    return info


def _read_npy(filespec):
    with open(filespec, "rb") as npyfile:
        magic = npyfile.read(6)
        assert magic == b"\x93NUMPY", "Not a valid numpy file"
        _ = npyfile.read(2)  # version number; ignore
        header_size, = struct.unpack("<h", npyfile.read(2))
        header = npyfile.read(header_size)
        meta = ast.literal_eval(header.decode("utf-8"))
        dtype = np.dtype(meta["descr"])
        shape = meta["shape"]
        if len(shape) in [2, 3]:  # grayscale or color
            info = ImageInfo()
            info.filespec = filespec
            info.filetype = "npy"
            info.cfa_raw = False
            info.packed_raw = False
            info.height, info.width = shape[:2]
            info.nchan = 1 if len(shape) < 3 else shape[2]
            info.isfloat = np.issubdtype(dtype, np.floating)
            info.bytedepth = dtype.itemsize
            info.bitdepth = info.bytedepth * 8
            info.maxval = 1.0 if info.isfloat else 2 ** info.bitdepth - 1
            info = _complete(info)
            return info
    raise ImageFileError(f"File {filespec} is not a valid NPY image file.")


def _complete(info):
    info.filesize = info.filesize or os.path.getsize(info.filespec)
    info.mipi_raw = info.mipi_raw and info.packed_raw
    info.maxval = info.maxval or 2 ** info.bitdepth - 1
    info.bitdepth = info.bitdepth or int(math.log2(info.maxval + 1))
    info.bytedepth = info.bytedepth or (2 if info.maxval > 255 else 1)
    if None not in [info.width, info.height]:
        info.npixels = info.width * info.height
        info.nbytes = info.npixels * info.nchan * info.bytedepth
        info.stride = info.stride or info.width * info.bytedepth
    info.uncertain = False if info.uncertain is None else info.uncertain
    info.orientation = info.orientation or 0  # None => 0
    info.rot90_ccw_steps = info.rot90_ccw_steps or 0  # None => 0
    info.header_size = info.header_size or 0  # None => 0
    if not info.multi_picture:
        info.multi_picture = False
        info.num_images = 1
        info.image_sizes = [info.filesize]
        info.image_offsets = [0]
    return info
