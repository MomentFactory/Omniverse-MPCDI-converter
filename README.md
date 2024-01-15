# mf.ov.mpcdi_converter

An Omniverse extension for MPDCI files.
Support MPCDI* to OpenUSD conversion as well as References to MPDCI files through a native USD FileFormat plugin.

MPCDI* is a VESA interchange format for videoprojectors technical data.

*Multiple Projection Common Data Interchange
MPCDIv2 is under Copyright © 2013 – 2015 Video Electronics Standards Association. All rights reserved.

## Requirements

- Requires Omniverse Kit >= 105.1
- Tested in USD Composer 2023.2.2 and 2023.2.0

## Build

The extension comes pre-built for Omniverse users but here are the steps if you want to build it by yourself.

### Build DLL for Omniverse

Just run `build.bat`.

### Test in Omniverse

1. `Window` > `Extensions`
2. ☰ > Settings
3. ✚ Add `_install\windows-x86_64\release` folder to the Extension Search Paths
4. The user extension should appear on the left
5. `Autoload` needs to be checked for the FileFormat plugin to be correctly loaded at USD Runtime.

### Build DLL for USDview

The dependency configuration is contained in the [usd-deps.packman.xml](deps/usd-deps.packman.xml) file
To switch to the correct OpenUSD version for USDview compilation, it is required to edit the packman configuration file to:

```
<project toolsVersion="5.6">
  <dependency name="nv-usd" linkPath="../_build/usd-deps/nv-usd/${config}">
    <package name="usd.py310.${platform}.usdview.${config}" version="0.23.05-tc.47+v23.05.b53573ea" />
  </dependency>
  <dependency name="python" linkPath="../_build/usd-deps/python">
    <package name="python" version="3.10.13+nv1-${platform}" />
  </dependency>
</project>
```

Then build as usual with `./build.bat`

To run USDview :
- `source setenvwindows`
- `usdview resource/scene.usda`

### Other OpenUSD compatible platforms

Waiting for an improved build process, we documented how you can build for other platforms (Unreal, Blender) in [this repo](https://github.com/MomentFactory/Omniverse-MVR-GDTF-converter).

## Using the extension

Enable the Extension ( `Window` > `Extensions` from USD Composer ).
[A sample MPCDI file](./exts/mf.ov.mpcdi_converter/mf/ov/mpcdi_converter/sample/Cube-mapping.mpcdi.xml) is provided.

### Reference an MPCDI file
To reference an MPCDI file, just drag and drop the file on your viewport or your Stage Window.

### Convert an MPCDI file

Three ways to convert from USD Composer :
1. `File` > `Import`.

Or from the Content window :

2. `+Import` button.
3. Right click > `Convert to USD` on an `.mpcdi.xml` file.

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

## Known issues

- While USD Cameras support Lens shift through the `offset`, the `RectLight` used to simulate the projector light does not offer such feature yet.
- Does not support yet the full MPCDI zip archive, only `.mpcdi.xml`
- XML extension usage : Fileformat plugin doesn't support having multiple extenions such as .mpcdi.xml (while Omniverse allows it). Currently this extension uses the .xml extension, which is not very convenient.