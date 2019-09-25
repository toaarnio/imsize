#!/usr/bin/python3 -B

import os              # built-in library
import math            # built-in library
import pprint          # built-in library
import piexif          # pip install piexif
import rawpy           # pip install rawpy
import numpy as np     # pip install numpy

try:
    # package mode
    from imsize import pnghdr   # local import: pnghdr.py
    from imsize import jpeghdr  # local import: jpeghdr.py
    from imsize import pnmhdr   # local import: pnmhdr.py
    from imsize import pfmhdr   # local import: pfmhdr.py
except ImportError:
    # stand-alone mode
    import pnghdr
    import jpeghdr
    import pnmhdr
    import pfmhdr


######################################################################################
#
#  P U B L I C   A P I
#
######################################################################################


class ImageInfo:
    """
    A container for image metadata, filled in and returned by read().

    Attributes:
      filespec (str): The filespec given to read(), copied verbatim
      filetype (str): File type: png|pnm|pfm|jpeg|insp|tiff|webp|dng|cr2|nef|raw
      filesize (int): Size of the file on disk in bytes
      isfloat (bool): True if the image is in floating-point format
      cfa_raw (bool): True if the image is in CFA (Bayer) raw format
      width (int): Width of the image in pixels (orientation ignored)
      height (int): Height of the image in pixels (orientation ignored)
      nchan (int): Number of color channels: 1, 2, 3 or 4
      bitdepth (int): Bits per sample: 1 to 32
      bytedepth (int): Bytes per sample: 1, 2 or 4
      maxval (int): Maximum representable sample value, e.g., 255
      nbytes (int): Size of the image in bytes, uncompressed
      uncertain (bool): True if width/height/bitdepth are uncertain
    """
    def __init__(self):
        self.filespec = None
        self.filetype = None
        self.filesize = None
        self.isfloat = None
        self.cfa_raw = None
        self.width = None
        self.height = None
        self.nchan = None
        self.bitdepth = None
        self.bytedepth = None
        self.maxval = None
        self.nbytes = None
        self.uncertain = None

    def __repr__(self):
        classname = self.__class__
        elements = self.__dict__
        reprstr = f"<ImageInfo {self.__dict__}>"
        return reprstr

    def __str__(self):
        infostr = pprint.pformat(self.__dict__)
        return infostr


def read(filespec):
    """
    Parses a lowest common denominator set of metadata from the given
    image, i.e., the dimensions and bit depth. Does not read the entire
    file but only what's necessary. Returns an ImageInfo with all fields
    filled in, or None in case of failure.

    Example:
      info = imsize.read("myfile.jpg")
      factor = info.nbytes / info.filesize
      print(f"{info.filespec}: compression factor = {factor.1f}")
    """
    filename = os.path.basename(filespec)             # "path/image.ext" => "image.ext"
    extension = os.path.splitext(filename)[-1]        # "image.ext" => ("image", ".ext")
    filetype = extension.lower()[1:]                  # ".EXT" => "ext"
    handlers = {"png": _read_png,
                "pnm": _read_pnm,
                "pgm": _read_pnm,
                "ppm": _read_pnm,
                "pfm": _read_pfm,
                "jpeg": _read_jpeg,
                "jpg": _read_jpeg,
                "insp": _read_insp,
                "tiff": _read_tiff,
                "tif": _read_tiff,
                "webp": _read_webp,
                "dng": _read_dng,
                "cr2": _read_cr2,
                "nef": _read_nef,
                "raw": _read_raw}
    if filetype in handlers:
        handler = handlers[filetype]
        info = handler(filespec)
        return info
    return None


######################################################################################
#
#  I N T E R N A L   F U N C T I O N S
#
######################################################################################


def _read_png(filespec):
    header = pnghdr.Png.from_file(filespec)
    colortype = pnghdr.Png.ColorType
    nchannels = {colortype.greyscale: 1,
                 colortype.truecolor: 3,
                 colortype.indexed: 3,
                 colortype.greyscale_alpha: 2,
                 colortype.truecolor_alpha: 4}
    info = ImageInfo()
    info.filespec = filespec
    info.filetype = "png"
    info.isfloat = False
    info.cfa_raw = False
    info.width = header.ihdr.width
    info.height = header.ihdr.height
    info.nchan = nchannels[header.ihdr.color_type]
    info.bitdepth = header.ihdr.bit_depth
    info = _complete(info)
    return info


def _read_pnm(filespec):
    shape, maxval = pnmhdr.dims(filespec)
    info = ImageInfo()
    info.filespec = filespec
    info.filetype = "pnm"
    info.isfloat = False
    info.cfa_raw = False
    info.width = shape[1]
    info.height = shape[0]
    info.nchan = 1 if len(shape) < 3 else shape[2]
    info.maxval = maxval
    info = _complete(info)
    return info


def _read_pfm(filespec):
    shape, maxval = pfmhdr.dims(filespec)
    info = ImageInfo()
    info.filespec = filespec
    info.filetype = "pfm"
    info.isfloat = True
    info.cfa_raw = False
    info.width = shape[1]
    info.height = shape[0]
    info.nchan = 1 if len(shape) < 3 else shape[2]
    info.maxval = maxval
    info.isfloat = True
    info.bitdepth = 32
    info.bytedepth = 4
    info = _complete(info)
    return info


def _read_jpeg(filespec):
    info = ImageInfo()
    info.filespec = filespec
    info.filetype = "jpeg"
    info.isfloat = False
    info.cfa_raw = False
    data = jpeghdr.Jpeg.from_file(filespec)
    for seg in data.segments:
        if seg.marker == seg.MarkerEnum.sof0:
            info.width = seg.data.image_width
            info.height = seg.data.image_height
            info.nchan = seg.data.num_components
            info.bitdepth = seg.data.bits_per_sample
            info = _complete(info)
            break
    return info


def _read_insp(filespec):
    info = _read_jpeg(filespec)
    info.filetype = "insp"
    return info


def _read_exif(filespec):
    try:
        exif = piexif.load(filespec)
        exif = exif.pop("0th")
        info = ImageInfo()
        info.filespec = filespec
        info.filetype = "exif"
        info.isfloat = False
        info.cfa_raw = exif.get(piexif.ImageIFD.PhotometricInterpretation) in [32803, 34892]
        info.width = exif.get(piexif.ImageIFD.ImageWidth)
        info.height = exif.get(piexif.ImageIFD.ImageLength)
        info.nchan = exif.get(piexif.ImageIFD.SamplesPerPixel)
        info.bitdepth = exif.get(piexif.ImageIFD.BitsPerSample)
        if isinstance(info.bitdepth, tuple):
            info.nchan = len(info.bitdepth)
            info.bitdepth = info.bitdepth[0]
        info = _complete(info)
        return info
    except (TypeError, ValueError):
        print(f"Unable to parse {filespec}: missing/broken EXIF metadata.")
        return None


def _read_webp(filespec):
    info = _read_exif(filespec)
    info.filetype = "webp"
    return info


def _read_tiff(filespec):
    info = _read_exif(filespec)
    info.filetype = "tiff"
    return info


def _read_dng(filespec):
    info = _read_exif(filespec)
    info.filetype = "dng"
    return info


def _read_cr2(filespec):
    exif = piexif.load(filespec)
    exif = exif.pop("0th")
    info = ImageInfo()
    info.filespec = filespec
    info.filetype = "cr2"
    info.uncertain = True
    info.isfloat = False
    info.cfa_raw = True
    info.width = exif.get(piexif.ImageIFD.ImageWidth)
    info.height = exif.get(piexif.ImageIFD.ImageLength)
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
    info.bitdepth = int(minbits)  # will fail if image is very dark
    info = _complete(info)
    return info


def _read_raw(filespec):  # reading the whole file ==> SLOW
    info = ImageInfo()
    info.filespec = filespec
    info.filetype = "raw"
    info.uncertain = True  # width, height & bitdepth are guessed
    info.isfloat = False
    info.cfa_raw = True
    info.nchan = 1
    info.bytedepth = 2  # all sensors are at least 10-bit these days
    info.filesize = os.path.getsize(filespec)
    for aspect in [3/4, 2/3, 9/16]:  # try some typical aspect ratios
        numpixels = info.filesize / info.bytedepth
        info.height = math.sqrt(numpixels * aspect)
        info.width = numpixels / info.height
        isint = lambda v: int(v) == v
        if isint(info.width) and isint(info.height):
            info.width = int(info.width)
            info.height = int(info.height)
            break
    if info.width is None:
        print(f"Unable to guess the dimensions of {filespec}.")
        return None
    else:
        raw = np.fromfile(filespec, dtype='<u2')  # assume x86 byte order
        minbits = np.ceil(np.log2(np.max(raw)))  # 5, 6, 7, ..., 16
        minbits = np.ceil(minbits / 2) * 2  # 6, 8, 10, 12, ..., 16
        minbits = max(minbits, 10)  # 10, 12, 14, 16
        info.bitdepth = int(minbits)  # will fail if image is very dark
        info = _complete(info)
        return info


def _complete(info):
    info.filesize = info.filesize or os.path.getsize(info.filespec)
    info.maxval = info.maxval or 2 ** info.bitdepth - 1
    info.bitdepth = info.bitdepth or int(math.log2(info.maxval + 1))
    info.bytedepth = info.bytedepth or (2 if info.maxval > 255 else 1)
    info.nbytes = info.width * info.height * info.nchan * info.bytedepth
    info.uncertain = False if info.uncertain is None else info.uncertain
    return info
