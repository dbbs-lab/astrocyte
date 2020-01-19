import setuptools, os, glob
import astrocyte

print("Packaging astrocyte version", astrocyte.__version__)

with open("README.md", "r") as fh:
    long_description = fh.read()


if not os.getenv("RTD_BUILD"):
    data_files = {
        "include_package_data": True,
        "data_files": [
            (
                "templates",
                glob.glob(
                    os.path.join(os.path.dirname(__file__), "astrocyte", "templates", "*")
                ),
            )
        ],
    }
else:
    # We're in a ReadTheDocs build: don't add any data files.
    data_files = {}

setuptools.setup(
    name="astrocyte",
    version=astrocyte.__version__,
    author="Robin De Schepper",
    author_email="robingilbert.deschepper@unipv.it",
    description="Packager for Glia",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dbbs-lab/astrocyte",
    license="GPLv3",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    **data_files,
    entry_points={"console_scripts": ["astro = astrocyte.cli:astrocyte_cli"]},
    install_requires=[
        "nrn-glia>=0.1.8",
        "setuptools",
        "gitpython>=3.0.0",
        "twine>=3.0.0",
        "requests",
        "appdirs>=1.4.3",
    ],
)
