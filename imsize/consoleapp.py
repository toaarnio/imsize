#!/usr/bin/python3 -B

"""
Calculates the combined in-memory size of the given images by parsing
their header information. Runs very fast because only the header part
of a file is read from disk.
"""

import os              # built-in library
import sys             # built-in library
import glob            # built-in library
import imsize          # pip install imsize

try:
    # package mode
    from imsize import argv
except ImportError:
    # stand-alone mode
    import argv


FILETYPES = ["*.png", "*.pnm", "*.pgm", "*.ppm", "*.jpeg", "*.jpg", "*.insp", "*.tiff", "*.tif", "*.dng"]


def main():
    verbose = not argv.exists("--quiet")
    show_help = argv.exists("--help")
    argv.exitIfAnyUnparsedOptions()
    if show_help:
        print("Usage: imsize [options] [file-or-directory ...]")
        print()
        print("  Displays the dimensions and uncompressed sizes of the given images.")
        print("  Runs very fast because only the header part of a file is read from")
        print("  disk.")
        print()
        print("  options:")
        print("    --quiet             do not show per-image information")
        print("    --help              show this help message")
        print()
        print("  example:")
        print("    imsize ~/Pictures")
        print()
        print("  supported file types:")
        print("   ", '\n    '.join(FILETYPES))
        print()
        sys.exit(-1)
    else:
        if verbose:
            print("See 'imsize --help' for command-line options.")
        paths = sys.argv[1:] or ["."]  # scan current directory if no arguments
        filespecs = find_files(paths)
        scan_sizes(filespecs, verbose)


def find_files(paths):
    allfiles = []
    for path in paths:
        if os.path.isdir(path):
            for filetype in FILETYPES:
                allfiles += glob.glob(os.path.join(path, filetype))
                allfiles += glob.glob(os.path.join(path, filetype.upper()))
        elif os.path.isfile(path):
            allfiles += [path]
    return allfiles


def scan_sizes(filespecs, verbose):
    total_compressed = 0
    total_uncompressed = 0
    num_processed = 0
    for filespec in sorted(filespecs):
        info = imsize.read(filespec)
        basename = os.path.basename(filespec)
        if info is not None:
            num_processed += 1
            total_uncompressed += info.nbytes / 1024**2
            total_compressed += info.filesize / 1024**2
            if verbose:
                megs = info.nbytes / 1024**2
                print(f"{basename}: {info.width} x {info.height} x {info.nchan} x {info.bitdepth} bits => {megs:.1f} MB")
    print(f"Scanned {num_processed} images, total {total_compressed:.1f} MB compressed, {total_uncompressed:.1f} MB uncompressed")


if __name__ == "__main__":
    main()
