"""
Foobar -- this __init__.py docstring shouldn't be visible anywhere.
"""

from .imsize import read, ImageInfo
from .version import __version__

__all__ = ["read", "ImageInfo", "__version__"]
