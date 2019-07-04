from setuptools import setup, find_packages

import imsize


def read_deps(filename):
    with open(filename) as f:
        deps = f.read().split('\n')
        deps.remove("")
    return deps


setup(name='imsize',
      version=imsize.__version__,
      description='Lightning-fast extraction of image dimensions & bit depth.',
      url='http://github.com/toaarnio/imsize',
      author='Tomi Aarnio',
      author_email='tomi.p.aarnio@gmail.com',
      license='MIT',
      packages=find_packages(),
      install_requires=read_deps("requirements.txt"),
      entry_points={'console_scripts': ['imsize = imsize.consoleapp:main']},
      zip_safe=True)
