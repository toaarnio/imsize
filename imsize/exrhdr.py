"""
A minimal header parser for OpenEXR images, meant solely for querying the
dimensions and bit depth.
"""

import numpy as np  # pip install numpy


######################################################################################
#
#  P U B L I C   A P I
#
######################################################################################


def dims(filespec, verbose=False):
    """
    Returns the dimensions (width, height, number of channels, datatype, and bit depth)
    of the given EXR file.
    """
    with open(filespec, "rb") as f:
        if f.read(4) == b"\x76\x2f\x31\x01":  # EXR magic number
            version = np.frombuffer(f.read(4), dtype="<u4")[0]
            max_strlen = 256 if (version & 0x400) else 32
            got_channels = False
            got_dims = False
            while not (got_channels and got_dims):
                attr_name = _read_string_nul(f, max_strlen)
                _ = _read_string_nul(f, max_strlen)  # attr_type
                attr_size = np.frombuffer(f.read(4), dtype="<u4")[0]
                if attr_name == "channels":
                    nchan = 0
                    isfloat = False
                    bitdepth = 16
                    while not got_channels:
                        name = _read_string_nul(f, max_strlen)
                        if len(name) >= 1:
                            dtype = np.frombuffer(f.read(16), dtype="<u4")[0]
                            isfloat = isfloat or (dtype > 0)
                            bitdepth = max(bitdepth, 16 if dtype == 1 else 32)
                            nchan += 1
                        else:
                            got_channels = True
                elif attr_name == "dataWindow":
                    box = np.frombuffer(f.read(16), dtype="<i4")
                    xmin, ymin, xmax, ymax = box
                    width = xmax - xmin + 1
                    height = ymax - ymin + 1
                    got_dims = True
                else:
                    _ = f.seek(attr_size, 1)
            if verbose:
                print(f"Reading file {filespec} ", end='')
                print(f"(w={width}, h={height}, c={nchan}, bitdepth={bitdepth})")
            return width, height, nchan, isfloat, bitdepth
    raise RuntimeError(f"File {filespec} is not a valid EXR file.")


######################################################################################
#
#  I N T E R N A L   F U N C T I O N S
#
######################################################################################


def _read_string_nul(f, maxlen):
    cur = f.tell()
    chunk = f.read(maxlen)
    asbytes = chunk.split(b"\x00")[0]
    string = asbytes.decode("utf-8")
    cur += len(string) + 1
    f.seek(cur)
    return string
