"""
Extracts image dimensions, bit depth, and other basic metadata.
Runs very fast due to reading and parsing only the file header,
with the exception of proprietary camera RAW files.

Example:
  info = imsize.read("myfile.jpg")
  factor = info.nbytes / info.filesize
  print(f"{info.filespec}: compression factor = {factor.1f}")

https://github.com/toaarnio/imsize
"""

from .imsize import FILETYPES
from .imsize import ImageInfo
from .imsize import read
from .imsize import guess_dims
from .imsize import ImageFileError
from .version import __version__

__all__ = ["FILETYPES", "ImageFileError", "ImageInfo", "__version__", "guess_dims", "read"]
