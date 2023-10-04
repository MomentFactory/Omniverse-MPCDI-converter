# mf.ov.mpcdi_converter

An Omniverse extension for MPDCI files support.
Support MPCDI to USD conversion as well as References to MPDCI files through a native USD FileFormatPlugin.

MPCDI is a VESA interchange format for videoprojectors technical data.

## Getting started

- Requires Omniverse Kit >= 105
- Tested in USD Composer 2023.1.1 and 2023.2.0

## Using the extension

Enable the Extension ( `Window` > `Extensions` from USD Composer ).

[A sample MPCDI file](./exts/mf.ov.mpcdi_converter/mf/ov/mpcdi_converter/sample/Cube-mapping.mpcdi.xml) is provided.

### Referencing an MPCDI file

To reference an MPCDI file, just drag and drop the file on your viewport or your Stage Window. 

### Converting an MPCDI file

Three ways to convert from USD Composer :
1. `File` > `Import`.

Or from the Content window :

2. `+Import` button.
3. Right click > `Convert to USD` on an `.mpcdi.xml` file.

## Build the extension

The source code of the USD FileFormat plugin resides in a submodule pointing towards : https://github.com/MomentFactory/usd-mpcdi-plugin. 

The extension comes pre-built for Omniverse users but here are the steps if you want to build it by yourself.  

### Retrieve Submodule

`git submodule update --init`

### Build DLL

`build.bat`

### Insert DLL in built extension

Once the build is complete, a dll should be available following this path :

`_install/windows-x86_64/release/mpcdiFileFormat/lib/mpcdiFileFormat.dll`

Simply copy this dll into the extension folder by running : 

`cp _install/windows-x86_64/release/mpcdiFileFormat/lib/mpcdiFileFormat.dll exts/mf.ov.mpcdi_converter/plugin`

### Test Extension in Omniverse

1. `Window` > `Extensions`
2. ☰ > Settings
3. ✚ Add `exts/` folder to the Extension Search Paths
4. The user extension should appear on the left
5. `Autoload` needs to be checked for the FileFormat plugin to be correctly loaded at USD Runtime. 

## Implementation note
- Since they are no projectors in Omniverse, a projector will be represented as:
  - A camera with the frustum of the projector
    - A child `RectLight` with the correct frustum that represents the light emitted
	- A simple mesh to represent the physical projector box
- Each buffer is represented as a scope in the scene tree with each projector as a child.
- MPCDI \<Extensions\> are currently ignored
- The frustum of each projector is currently calculated with a focus distance of 2 unit and a focal length of 10.

## Resources
- [MPCDI Christie Digital Github](https://github.com/ChristieDigital/mpcdi/blob/master/MPCDI_explained.md)
- MPCDIv2 standard can be downloaded from [the VESA website](https://vesa.org/vesa-standards/)
- MPCDIv2 is under Copyright © 2013 – 2015 Video Electronics Standards Association. All rights reserved.

- [NVIDIA USD plugin example](https://github.com/NVIDIA-Omniverse/usd-plugin-samples)

*Multiple Projection Common Data Interchange

## Known issues

- While USD Cameras support Lens shift through the `offset`, the `RectLight` used to simulate the projector light does not offer such feature yet. 
- Does not support yet the full MPCDI zip archive, only `.mpcdi.xml`