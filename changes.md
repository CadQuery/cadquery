Changes
=======

Master
------
   ### Breaking changes
   * Fixed bug in ParallelDirSelector where non-planar faces could be selected. Note this will be breaking if you've used DirectionNthSelector and a non-planar face made it into your object list. In that case eg. ">X[2]" will have to become ">X[1]".

2.1RC1 (release candidate)
------
   ### Breaking changes
   * `centerOption` default value changed from `CenterOfMass` to `ProjectedOrigin` #532

   ## Other changes

   * Simplified `largestDimension()` bounding box check #317
   * Added `FontPath` to `makeText()` #337
   * Support for slicing (`section()`) of models #339 #349
   * Added DXF import (relies on ezdxf) #351 #372 #406 #442
   * Added DXF export #415 #419 #455
   * Exposed `angularPrecision` parameter in `exportStl()` #329
   * Fixed bug in `makeRuled()` #329
   * Made solid construction from `shell()` more robust #329
   * Added CadQuery logos to docs #329
   * Added `toPending()` to allow adding wires/edges to `pendingWires`/`pendingEdges` #351
   * Implemented `glue` parameter for `fuse()` #375
   * Exposed parameters for fuzzy bool operations #375
   * Started using MyPy in CI and type annotations #378 #380 #391
   * Implemented a `Location` class #380
   * Merged `CQ` class into `Workplane` to eliminate duplicated code #380
   * Added additional parameters for `BuildCurves3d_s` method #387
   * Implemented fully closed shelling #394
   * Refactored `polarArray()` #395
   * Improved local rotation handling #395
   * Implemented 2D offset in `offset2D` #397
   * Added `locationAt()` to generate locations along a curve #404
   * Added DOI to README for references in research papers #412
   * Changed `shell()` to set `Intersection` parameter to `True` #411
   * Exposed joint type (`kind`) for `shell()` #413
   * Refactored exporters #415
   * Started using `find_packages()` in setup.py #418
   * Tessellation winding fix #420
   * Added `angularPrecision` to `export`, `exportShape` and `toString` #424
   * Added py.typed file for PEP-561 compatibility #435
   * Added assembly API with constraint solver #440 #482 #545 #556
   * Integrated sphinxcadquery to add 3D visualization of parts to docs #111
   * Allow spaces in Vector literal #445
   * Added export to OCCT native CAF format #440
   * Implemented color export in STEP generated from assemblies #440
   * Added ability to set `fontPath` parameter for `text()` #453
   * Now protect against `rarray()` spacings of 0 #454
   * Changed Nth selector rounding `self.TOLERANCE` calculation to produce 4 decimal places #461
   * Fixed `parametricCurve()` to use correct stop point #477
   * Excluded tests from installation in setup.py #478
   * Added `mesh()` method to shapes.py #482
   * Added VRML export #482
   * Implemented ability to create a child workplane on the vertex #480
   * Improved consistency in handling of BoundaryBox tolerance #490
   * Implemented `locations()` for Wires #475
   * Exposed mode for sweep operations #496
   * Added 'RadiusNthSelector()` #504
   * Added tag-based constraint definition for assemblies #514
   * Implemented ability to mirror from a selected face #527
   * Improved edge selector tests #541
   * Added `glue` parameter to `combine()` #535
   * Finally fixed github-linguist statistics #547
   * Updated for Python 3.8
   * Numerous documentation updates and example additions

2.0 (stable release)
------

### Deprecations and breaking changes
   * `centerOption` default value will change from `CenterOfMass` to `ProjectedOrigin` in the 2.1 release #313

### Non-breaking changes

   * Numerous commits to move from FreeCAD as the underlying API to PythonOCC - thanks @adam-urbanczyk for all the effort that required
   * Updated for Python 3.6 and 3.7
   * Made sure solids were fused when extrude both=True #321 - thanks @adam-urbanczyk
   * Improved boolean operations #312 - thanks @adam-urbanczyk
   * Fixed a bug in helix creation #311 - thanks @adam-urbanczyk
   * Improved MacOS support
   * Updated CQGI counters for Python 3.8 compatibility #305 - thanks @jwhevans
   * Added tangent arc operation #284 - thanks @marcus7070
   * Added ellipse creation #265 - thanks @bernhard-42
   * Added ability to produce a plate surface with a thickness (optional), enclosed by edge points, polylines or splines, and going through interpolation points (optional) #253 - thanks @bragostin
   * Fix plane rotation method #243 - thanks @Peque
   * Added ability to tag a particular object in the chain to be referred to later #252 - thanks @marcus7070
   * Added Black formatting check to CI #255 - thanks @Peque
   * Added ability to accept unordered edges when constructing a wire #237 - thanks @bragostin
   * Updated to using pytest #236 - thanks @Peque
   * Fixed wedge primitive and made wedge act consistent with other primitives #228
   * Fix to correctly support anisotropic scaling #225 - thanks @adam-urbanczyk
   * Documentation fixes #215 - thanks @Renha
   * Fixed a spline example in the docs #200 - thanks @adam-urbanczyk
   * Added 2D slot feature #186 - thanks @bweissinger
   * Fixed a segmentation fault when trying to loft with one wire #161 - thanks @HLevering
   * Fixed a bug where the tolerance parameter of BoundingBox had no effect #167 - thanks @mgreminger
   * Fixed a bug when calling findSolid with multiple solids on stack #163 - thanks @adam-urbanczyk
   * Documentation fixes #144 and #162 - thanks @westurner
   * Fixed a feature/bug that prevented a polyline or spline from closing properly in some instances #156 - thanks @adam-urbanczyk
   * Added ability to determine if an arbitrary point is inside a solid #138 - thanks @mgreminger
   * Fixed bug where combine=True kept union from working properly #143 - thanks @adam-urbanczyk
   * Fixed bug where string selectors "-X" and "+X" returned the same thing #141 - thanks @gebner
   * Removed unused 'positive' argument from 'cutThruAll' #135 - thanks @mgreminger
   * Increased the HASH_CODE_MAX to prevent hash collisions during face selection #140 - thanks @mgreminger
   * Added option to center workplane on projected origin #132 - thanks @mgreminger
   * Improved sweep along multisection wires #128 - thanks @adam-urbanczyk
   * Fixed version number that was missed during update to 2.x #129 - thanks @asukiaaa
   * Numerous CI and documentation improvements
   * Support for text rendering #106

2.0RC2 (release candidate)
------
   * Changes included in v2.0 release

2.0RC1 (release candidate)
------
   * Changes included in v2.0 release

2.0RC0 (release candidate)
------
   * Changes included in v2.0 release

The changelog for older CadQuery 1.x releases can be found [here](https://github.com/dcowden/cadquery/blob/master/changes.md).
