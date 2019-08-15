"""
A minimal header parser for PFM images, meant solely for querying the
dimensions and bit depth.
"""

import re  # built-in library


######################################################################################
#
#  P U B L I C   A P I
#
######################################################################################

def dims(filespec, verbose=False):
    """
    Returns the dimensions (width, height, and number of channels) of the given
    PGM/PPM file. Also returns the maximum representable value of a pixel
    (typically 255, 1023, 4095, or 65535).
    """
    with open(filespec, "rb") as f:
        header = f.read(64)  # should be enough for any valid header
        shape, maxval = __parse_header(header, filespec, verbose)
        return (shape, maxval)


######################################################################################
#
#  I N T E R N A L   F U N C T I O N S
#
######################################################################################


def __parse_header(header, filespec, verbose=False):
    regex_pfm_header = b"(^(P[Ff])\\s+(\\d+)\\s+(\\d+)\\s+([+-]?\\d+(?:\\.\\d+)?)\\s)"
    match = re.search(regex_pfm_header, header)
    if match is not None:
        header, typestr, width, height, scale = match.groups()
        width, height, scale = int(width), int(height), float(scale)
        numch = 3 if typestr == b"PF" else 1
        shape = (height, width, numch) if numch == 3 else (height, width)
        dtype = "<f" if scale < 0.0 else ">f"
        scale = abs(scale)
        if verbose:
            print(f"Reading file {filespec} ", end='')
            print(f"(w={width}, h={height}, c={numch}, scale={scale:.3f}, byteorder='{dtype[0]}')")
        return (shape, scale)
    raise RuntimeError(f"File {filespec} is not a valid PFM file.")
