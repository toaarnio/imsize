#!/usr/bin/python3 -B

"""
Calculates the combined in-memory size of the given images by parsing
their header information. Runs very fast because only the header part
of a file is read from disk (except for headerless Camera RAW and Nikon
NEF).
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


FILETYPES = ["*.png", "*.pnm", "*.pgm", "*.ppm", "*.pfm", "*.bmp",
             "*.jpeg", "*.jpg", "*.insp", "*.tiff", "*.tif", "*.hdr",
             "*.exr", "*.dng", "*.cr2", "*.nef", "*.raw", "*.npy"]


def main():
    """
    Entry point for the 'imsize' command-line application.
    """
    show_all = argv.exists("--all")
    verbose = not argv.exists("--quiet")
    show_help = argv.exists("--help")
    argv.exitIfAnyUnparsedOptions()
    if show_help:
        print("Usage: imsize [options] [file-or-directory ...]")
        print()
        print("  Displays the dimensions and uncompressed sizes of the given images.")
        print("  Runs very fast because only the header part of a file is read from")
        print("  disk (except for headerless Camera RAW and Nikon NEF).")
        print()
        print("  options:")
        print("    --all               show all extracted per-image metadata")
        print("    --quiet             do not show per-image information")
        print("    --help              show this help message")
        print()
        print("  example:")
        print("    imsize ~/Pictures")
        print()
        print("  supported file types:")
        print("   ", '\n    '.join(FILETYPES))
        print()
        print(f"imsize version {imsize.__version__}")
        print()
        sys.exit(-1)
    else:
        if verbose:
            print("See 'imsize --help' for command-line options.")
        paths = sys.argv[1:] or ["."]  # scan current directory if no arguments
        filespecs = find_files(paths)
        scan_sizes(filespecs, verbose, show_all)


def find_files(paths):
    """
    Collects all files with known filetypes from the given list of directories.
    """
    allfiles = []
    for path in paths:
        if os.path.isdir(path):
            for filetype in FILETYPES:
                allfiles += glob.glob(os.path.join(path, filetype))
                allfiles += glob.glob(os.path.join(path, filetype.upper()))
        elif os.path.isfile(path):
            allfiles += [path]
    return allfiles


def scan_sizes(filespecs, verbose, show_all):
    """
    Displays the dimensions of the given list of images.
    """
    total_compressed = 0
    total_uncompressed = 0
    num_processed = 0
    for filespec in sorted(filespecs):
        basename = os.path.basename(filespec)
        try:
            info = imsize.read(filespec)
        except Exception as e:
            print(f"{basename}: {type(e).__name__}: {e}")
            continue
        if info.width is None:
            print(f"{basename}: Unable to guess dimensions. Maybe not an image? Skipping.")
        else:
            num_processed += 1
            total_uncompressed += info.nbytes / 1024**2
            total_compressed += info.filesize / 1024**2
            if verbose:
                megs = info.nbytes / 1024**2
                mpix = info.width * info.height / 1000000
                est = " [estimated]" if info.uncertain else ""
                if info.rot90_ccw_steps in [0, 2]:
                    width, height = (info.width, info.height)
                else:
                    width, height = (info.height, info.width)
                print(f"{basename}: {width} x {height} x {info.nchan} x {info.bitdepth} bits => {megs:.1f} MB{est}, {mpix:.1f} MP")
            if show_all:
                print(info)
    print(f"Scanned {num_processed} images, total {total_compressed:.1f} MB compressed, {total_uncompressed:.1f} MB uncompressed")


if __name__ == "__main__":
    main()
