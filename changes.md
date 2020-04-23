Changes
=======

2.0 (stable release)
------
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
   * Increased the HASH_CODE_MAX to prevent hash collisions during face selection #140 - - thanks @mgreminger
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
