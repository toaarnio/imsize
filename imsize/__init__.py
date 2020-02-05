"""
Extracts image dimensions, bit depth, and other basic metadata.

Example:
  info = imsize.read("myfile.jpg")
  factor = info.nbytes / info.filesize
  print(f"{info.filespec}: compression factor = {factor.1f}")

https://github.com/toaarnio/imsize
"""

from .imsize import read, ImageInfo

__version__ = "1.0.3"
__all__ = ["read", "ImageInfo"]
