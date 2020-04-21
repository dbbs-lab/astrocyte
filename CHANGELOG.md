# Version 0.2

## 0.2.3

* Raised minimum glia versions to 0.1.10

## 0.2.2

* Added support for ARTIFICIAL_CELL mods.

## 0.2.1

* Fixed `astro edit` command

## 0.2.0

* Added the `add mod --local`: Installs mod files locally for use on the local machine.
* Fixed various bugs that occured when using Astrocyte in another folder than the current
  working directory.

# Version 0.1

## 0.1.1

* Fixed a bug that always added a POINT_PROCESS statement when adding mod files.

## 0.1.0

* Astro can authenticate you with the package repository and stores the
  authentication token.
* Astro will upload metadata to the package repository when using `astro upload`.

# Version 0

## 0.0.6

* You can import `point_process`es using `astro add mod`.

## 0.0.5

* You can edit the name and variant of existing assets.
* You can use `astro uninstall` to uninstall the currently built distribution.

## 0.0.4

* You can specify an asset name and variant name when adding mod files.
* A git repository is created for you when the package is created.
* Git commits are made when adding mod files.

## 0.0.1

* First release of Astrocyte.
* Astrocyte can create, build and upload packages to PyPI that are discoverable
  by Glia.
* Astrocyte can import mod files and updates package information.
* Astrocyte modifies mod files on import to adhere to Glia naming convention.
