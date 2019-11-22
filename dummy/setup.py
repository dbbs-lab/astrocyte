import setuptools, os, glob
from dummy import __version__

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
     name='dummy',
     version=__version__,
     author="d",
     author_email="d",
     description="Glia package of NEURON models",
     long_description=long_description,
     long_description_content_type="text/markdown",
     url="https://github.com/dbbs-lab/glia",
     license='GPLv3',
     packages=setuptools.find_packages(),
     classifiers=[
         "Programming Language :: Python :: 3",
         "Operating System :: OS Independent",
     ],
     include_package_data=True,
     data_files=[
         ('mod', glob.glob(os.path.join(os.path.dirname(__file__), "dummy", "mod", "*")))
     ],
     entry_points={
      'glia.package': ['dummy = dummy']
     },
     install_requires=[
      "nrn-glia>=0.0.1-a5"
     ]
 )
