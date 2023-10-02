# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.0.7] - 2023-05-17
- Fix reading files from Nucleus (OM-93104)

## [1.0.5] - 2023-05-02
- RTX on/off option

## [1.0.4] - 2023-03-31
- Report E57 import error to a modal prompt

## [1.0.3] - 2023-03-21
- Fix scan combine and centering during USD save

## [1.0.2] - 2023-03-21
- Fix carb::tasking not loaded

## [1.0.0] - 2023-03-18
### Changes
- Async and multithreaded import
- Point transforms are kept in scan's xforms (OM-52424)

## [0.2.0] - 2023-03-14
### Changes
Python 3.10 and USD 22.22 update

## [0.1.12] - 2023-02-13
### Changes
Optimization of import time

## [0.1.11] - 2023-01-23
### Changes
Correct transformation from rotation (OM-79045)

## [0.1.10] - 2023-01-20
### Changes
Display color interpolation set to vertex (OM-72158)

## [0.1.9] - 2023-01-16
### Added
Kit 104 support

## [0.1.7] - 2021-12-07
### Changes
Import normals in e57 files when available

## [0.1.6] - 2021-08-23
### Changes
Use intensity as color when no color information is available.
- Fixes OM-35881

## [0.1.5] - 2021-07-16
### Changes
Fix linux runtime linker errors.

## [0.1.4] - 2021-06-23
### Changes
Fix affine matrix for pose transformations.

## [0.1.3] - 2021-06-18
### Changes
Apply pose transformations (if it exists).

## [0.1.2] - 2021-06-18
### Changes
- Changes to ordering config (was not loading early enough in Kit 101)
- Build for kit-sdk 102, drop kit-sdk 101 because of ordering problem
- better memory allocation strategies
- Create default xform as parent for scans

## [0.1.1] - 2021-05-18
### Changes
- Bundle dependent licenses in packaged extensions

## [0.1.0] - 2021-02-05
### Added
- Initial Release
