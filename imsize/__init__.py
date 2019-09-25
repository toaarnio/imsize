"""
Extracts image dimensions & bit depth.

Example:
  info = imsize.read("myfile.jpg")
  factor = info.nbytes / info.filesize
  print(f"{info.filespec}: compression factor = {factor.1f}")

https://github.com/toaarnio/imsize
"""

from .imsize import *

__version__ = "0.9.2"
__all__ = ["read", "ImageInfo"]
