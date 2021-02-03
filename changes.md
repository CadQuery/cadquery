Changes
=======

2.1 (stable release)
------
   ### Breaking changes
   * Fixed bug in ParallelDirSelector where non-planar faces could be selected. Note this will be breaking if you've used DirectionNthSelector and a non-planar face made it into your object list. In that case eg. ">X[2]" will have to become ">X[1]".

   ### Other changes
   * Refactored selectors and added CenterNthSelector [#549](https://github.com/CadQuery/cadquery/pull/549)
   * Added new installation video links to the readme [#550](https://github.com/CadQuery/cadquery/pull/550)
   * Exposed `makeWire` in `parametricCurve()` [#555](https://github.com/CadQuery/cadquery/pull/555)
   * Fixed a `centerOption` bug in the assembly tutorial [#556](https://github.com/CadQuery/cadquery/pull/556)
   * Added `hLineTo`, `polarLine` and `polarLineTo` to autosummary [#561](https://github.com/CadQuery/cadquery/pull/561)
   * Updated workplane docstring for recent center option changes [#563](https://github.com/CadQuery/cadquery/pull/563)
   * Fixed indentation in CQContext docs [#571](https://github.com/CadQuery/cadquery/pull/571)
   * Indicated breaking changes and made docstring fixes [#573](https://github.com/CadQuery/cadquery/pull/573)
   * Fixed `split()` docstring [#574](https://github.com/CadQuery/cadquery/pull/574)
   * Updated the readthedocs CQ logo [#581](https://github.com/CadQuery/cadquery/pull/581)
   * Removed unused variable from counter-bore example [#584](https://github.com/CadQuery/cadquery/pull/584)
   * Fixed unconstrained `assembly.solve()` [#592](https://github.com/CadQuery/cadquery/pull/592)
   * Added an example for `cq.Wire.makeHelix()` [#594](https://github.com/CadQuery/cadquery/pull/594)
   * Exposed additional SVG options to exporters interface [#596](https://github.com/CadQuery/cadquery/pull/596)
   * Fixed `ellipse()` documentation formatting [#597](https://github.com/CadQuery/cadquery/pull/597)
   * Fixed `cutThruAll()` when working with non-planar faces [#604](https://github.com/CadQuery/cadquery/pull/604)
   * Fixed `center` option in `rect()` call in tests [#607](https://github.com/CadQuery/cadquery/pull/607)
   * Fixed examples and enabled them in the test suite [#609](https://github.com/CadQuery/cadquery/pull/609)
   * Fixed wedge centering [#611](https://github.com/CadQuery/cadquery/pull/611) and [#613](https://github.com/CadQuery/cadquery/pull/613)
   * Updated assembly documentation [#614](https://github.com/CadQuery/cadquery/pull/614)

2.1RC1 (release candidate)
------
   ### Breaking changes
   * `centerOption` default value changed from `CenterOfMass` to `ProjectedOrigin` [#532](https://github.com/CadQuery/cadquery/pull/532)
   * `Wire.combine` interface changed - now it returns `List[Wire]` [#397](https://github.com/CadQuery/cadquery/pull/397)
   * `Workplane.each` interface changed - callable of the `Callable[[Union[cadquery.occ_impl.geom.Vector, cadquery.occ_impl.geom.Location, cadquery.occ_impl.shapes.Shape]], cadquery.occ_impl.shapes.Shape]` type is required [#391](https://github.com/CadQuery/cadquery/pull/391)

   ### Other changes

   * Simplified `largestDimension()` bounding box check [#317](https://github.com/CadQuery/cadquery/pull/317)
   * Added `FontPath` to `makeText()` [#337](https://github.com/CadQuery/cadquery/issues/337)
   * Support for slicing (`section()`) of models [#339](https://github.com/CadQuery/cadquery/pull/339) [#349](https://github.com/CadQuery/cadquery/pull/349)
   * Added DXF import (relies on ezdxf) [#351](https://github.com/CadQuery/cadquery/pull/351) [#372](https://github.com/CadQuery/cadquery/pull/372) [#406](https://github.com/CadQuery/cadquery/pull/406) [#442](https://github.com/CadQuery/cadquery/pull/442)
   * Added DXF export [#415](https://github.com/CadQuery/cadquery/pull/415) [#419](https://github.com/CadQuery/cadquery/pull/419) [#455](https://github.com/CadQuery/cadquery/pull/455)
   * Exposed `angularPrecision` parameter in `exportStl()` [#329](https://github.com/CadQuery/cadquery/pull/329)
   * Fixed bug in `makeRuled()` [#329](https://github.com/CadQuery/cadquery/pull/329)
   * Made solid construction from `shell()` more robust [#329](https://github.com/CadQuery/cadquery/pull/329)
   * Added CadQuery logos to docs [#329](https://github.com/CadQuery/cadquery/pull/329)
   * Added `toPending()` to allow adding wires/edges to `pendingWires`/`pendingEdges` [#351](https://github.com/CadQuery/cadquery/pull/351)
   * Implemented `glue` parameter for `fuse()` [#375](https://github.com/CadQuery/cadquery/pull/375)
   * Exposed parameters for fuzzy bool operations [#375](https://github.com/CadQuery/cadquery/pull/375)
   * Started using MyPy in CI and type annotations [#378](https://github.com/CadQuery/cadquery/pull/378) [#380](https://github.com/CadQuery/cadquery/pull/380) [#391](https://github.com/CadQuery/cadquery/pull/391)
   * Implemented a `Location` class [#380](https://github.com/CadQuery/cadquery/pull/380)
   * Merged `CQ` class into `Workplane` to eliminate duplicated code [#380](https://github.com/CadQuery/cadquery/pull/380)
   * Added additional parameters for `BuildCurves3d_s` method [#387](https://github.com/CadQuery/cadquery/pull/387)
   * Implemented fully closed shelling [#394](https://github.com/CadQuery/cadquery/pull/394)
   * Refactored `polarArray()` [#395](https://github.com/CadQuery/cadquery/pull/395)
   * Improved local rotation handling [#395](https://github.com/CadQuery/cadquery/pull/395)
   * Implemented 2D offset in `offset2D` [#397](https://github.com/CadQuery/cadquery/pull/397)
   * Added `locationAt()` to generate locations along a curve [#404](https://github.com/CadQuery/cadquery/pull/404)
   * Added DOI to README for references in research papers [#410](https://github.com/CadQuery/cadquery/pull/410)
   * Changed `shell()` to set `Intersection` parameter to `True` [#411](https://github.com/CadQuery/cadquery/pull/411)
   * Exposed joint type (`kind`) for `shell()` [#413](https://github.com/CadQuery/cadquery/pull/413)
   * Refactored exporters [#415](https://github.com/CadQuery/cadquery/pull/415)
   * Started using `find_packages()` in setup.py [#418](https://github.com/CadQuery/cadquery/pull/418)
   * Tessellation winding fix [#420](https://github.com/CadQuery/cadquery/pull/420)
   * Added `angularPrecision` to `export`, `exportShape` and `toString` [#424](https://github.com/CadQuery/cadquery/pull/424)
   * Added py.typed file for PEP-561 compatibility [#435](https://github.com/CadQuery/cadquery/pull/435)
   * Added assembly API with constraint solver [#440](https://github.com/CadQuery/cadquery/pull/440) [#482](https://github.com/CadQuery/cadquery/pull/482) [#545](https://github.com/CadQuery/cadquery/pull/545) [#556](https://github.com/CadQuery/cadquery/pull/556)
   * Integrated sphinxcadquery to add 3D visualization of parts to docs [#111](https://github.com/CadQuery/cadquery/pull/111)
   * Allow spaces in Vector literal [#445](https://github.com/CadQuery/cadquery/pull/445)
   * Added export to OCCT native CAF format [#440](https://github.com/CadQuery/cadquery/pull/440)
   * Implemented color export in STEP generated from assemblies [#440](https://github.com/CadQuery/cadquery/pull/440)
   * Added ability to set `fontPath` parameter for `text()` [#453](https://github.com/CadQuery/cadquery/pull/453)
   * Now protect against `rarray()` spacings of 0 [#454](https://github.com/CadQuery/cadquery/pull/454)
   * Changed Nth selector rounding `self.TOLERANCE` calculation to produce 4 decimal places [#461](https://github.com/CadQuery/cadquery/pull/461)
   * Fixed `parametricCurve()` to use correct stop point [#477](https://github.com/CadQuery/cadquery/pull/477)
   * Excluded tests from installation in setup.py [#478](https://github.com/CadQuery/cadquery/pull/478)
   * Added `mesh()` method to shapes.py [#482](https://github.com/CadQuery/cadquery/pull/482)
   * Added VRML export [#482](https://github.com/CadQuery/cadquery/pull/482)
   * Implemented ability to create a child workplane on the vertex [#480](https://github.com/CadQuery/cadquery/pull/480)
   * Improved consistency in handling of BoundaryBox tolerance [#490](https://github.com/CadQuery/cadquery/pull/490)
   * Implemented `locations()` for Wires [#475](https://github.com/CadQuery/cadquery/pull/475)
   * Exposed mode for sweep operations [#496](https://github.com/CadQuery/cadquery/pull/496)
   * Added 'RadiusNthSelector()` [#504](https://github.com/CadQuery/cadquery/pull/504)
   * Added tag-based constraint definition for assemblies [#514](https://github.com/CadQuery/cadquery/pull/514)
   * Implemented ability to mirror from a selected face [#527](https://github.com/CadQuery/cadquery/pull/527)
   * Improved edge selector tests [#541](https://github.com/CadQuery/cadquery/pull/541)
   * Added `glue` parameter to `combine()` [#535](https://github.com/CadQuery/cadquery/pull/535)
   * Finally fixed github-linguist statistics [#547](https://github.com/CadQuery/cadquery/pull/547)
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
