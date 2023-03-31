# mf.ov.mpcdi_converter

An Omniverse extension to convert MPDCI files to USD.

MPCDI is a VESA interchange format for videoprojectors technical data. 

## Getting started

- Requires Omniverse Kit >= 104.1
- Tested in Create 2022.3.3

## Converting an MPCDI file


[A sample MPCDI file](./exts/mf.ov.mpcdi_converter/mf/ov/mpcdi_converter/sample/Cube-mapping.mpcdi.xml) is provided.

the file naming extension must be `.mpcdi.xml`

- Enable the Extension.
- Three ways to Import from Create :
  - File > Import.
  - Or from the Content windows :
    - +Import button.
    - Right click > Convert to USD on an `.mpcdi.xml` file.

## Application statup

```
$ ./link_app.bat --app create
$ ./app/omni.create.bat --/rtx/ecoMode/enabled=false --ext-folder exts --enable mf.ov.mpcdi_converter
```

Or simply search for this community extension within the Extension Window of Create !

## Some Math

//TODO @Antoine ?

## Resources
- [MPCDI Christie Digital Github](https://github.com/ChristieDigital/mpcdi/blob/master/MPCDI_explained.md)
- MPCDIv2 standard can be downloaded from [the VESA website](https://vesa.org/vesa-standards/)
- MPCDIv2 is under Copyright © 2013 – 2015 Video Electronics Standards Association. All rights reserved.

*Multiple Projection Common Data Interchange

## Known issues

- So far, no way to Reference or Payload directly an `.mpcdi.xml` file.
- While USD Cameras support Lens shift through the `offset`, the `RectLight` used to simulate the projector light does not offer such feature yet.  
- Does not support yet the full MPCDI zip archive, only `.mpcdi.xml`