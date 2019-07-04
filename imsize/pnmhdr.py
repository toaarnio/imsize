"""
A minimal header parser for PNM/PGM/PPM images, meant solely for querying the
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
        header = f.readline()
        shape, maxval = __parse_header(header, filespec, verbose)
        return (shape, maxval)


######################################################################################
#
#  I N T E R N A L   F U N C T I O N S
#
######################################################################################


def __parse_header(header, filespec, verbose=False):
    regex_pnm_header = b"(^(P[56])\\s+(\\d+)\\s+(\\d+)\\s+(\\d+)\\s)"
    match = re.search(regex_pnm_header, header)
    if match is not None:
        header, typestr, width, height, maxval = match.groups()
        width, height, maxval = int(width), int(height), int(maxval)
        numch = 3 if typestr == b"P6" else 1
        shape = (height, width, numch) if typestr == b"P6" else (height, width)
        if verbose:
            print(f"Reading file {filespec} ", end='')
            print(f"(w={width}, h={height}, c={numch}, maxval={maxval})")
        return (shape, maxval)
    raise RuntimeError(f"File {filespec} is not a valid PGM/PPM file.")
