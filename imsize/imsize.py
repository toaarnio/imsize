#!/usr/bin/python3 -B

import os              # built-in library
import math            # built-in library
import piexif          # pip install piexif

try:
    # package mode
    from imsize import pnghdr   # local import: pnghdr.py
    from imsize import jpeghdr  # local import: jpeghdr.py
    from imsize import pnmhdr   # local import: pnmhdr.py
except ImportError:
    # stand-alone mode
    import pnghdr
    import jpeghdr
    import pnmhdr


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
      filetype (str): File type: "png", "pnm", "jpeg" or "exif"
      filesize (int): Size of the file on disk in bytes
      width (int): Width of the image in pixels (orientation ignored)
      height (int): Height of the image in pixels (orientation ignored)
      nchan (int): Number of color channels: 1, 2, 3 or 4
      bitdepth (int): Bits per sample: 1 to 16
      bytedepth (int): Bytes per sample: 1 or 2
      maxval (int): Maximum representable sample value, e.g., 255
      nbytes (int): Size of the image in bytes, uncompressed
    """
    def __init__(self):
        self.filespec = None
        self.filetype = None
        self.filesize = None
        self.width = None
        self.height = None
        self.nchan = None
        self.bitdepth = None
        self.bytedepth = None
        self.maxval = None
        self.nbytes = None


def read(filespec):
    """
    Parses a lowest common denominator set of metadata from the given
    PNG/PNM/JPEG/TIFF image, i.e., the dimensions and bit depth. Does
    not read the entire file but only what's necessary. Returns an
    ImageInfo with all fields filled in, or None in case of failure.

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
                "jpeg": _read_jpeg,
                "jpg": _read_jpeg,
                "tiff": _read_exif,
                "tif": _read_exif,
                "webp": _read_exif}
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
    info.width = shape[1]
    info.height = shape[0]
    info.nchan = shape[2]
    info.maxval = maxval
    info = _complete(info)
    return info


def _read_exif(filespec):
    try:
        exif = piexif.load(filespec).pop("0th")
        info = ImageInfo()
        info.filespec = filespec
        info.filetype = "exif"
        info.width = exif.get(piexif.ImageIFD.ImageWidth)
        info.height = exif.get(piexif.ImageIFD.ImageLength)
        info.nchan = exif.get(piexif.ImageIFD.SamplesPerPixel)
        info.bitdepth = exif.get(piexif.ImageIFD.BitsPerSample)[0]
        info = _complete(info)
        return info
    except TypeError:
        print(f"Unable to parse {filespec}: missing/broken EXIF metadata.")
        return None


def _read_jpeg(filespec):
    info = ImageInfo()
    info.filespec = filespec
    info.filetype = "jpeg"
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


def _complete(info):
    info.filesize = os.path.getsize(info.filespec)
    info.maxval = info.maxval or 2 ** info.bitdepth - 1
    info.bitdepth = info.bitdepth or int(math.log2(info.maxval + 1))
    info.bytedepth = 2 if info.maxval > 255 else 1
    info.nbytes = info.width * info.height * info.nchan * info.bytedepth
    return info
