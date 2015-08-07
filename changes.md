Changes
=======


v0.1
-----
    * Initial Version

v0.1.6
-----
    * Added STEP import and supporting tests

v0.1.7
-----
    * Added revolve operation and supporting tests
    * Fixed minor documentation errors

v0.1.8
-----
    * Added toFreecad() function as a convenience for val().wrapped
    * Converted all examples to use toFreecad()
    * Updated all version numbers that were missed before
    * Fixed import issues in Windows caused by fc_import
    * Added/fixed Mac OS support
    * Improved STEP import
    * Fixed bug in rotateAboutCenter that negated its effect on solids
    * Added Travis config (thanks @krasin)
    * Removed redundant workplane.py file left over from the PParts.com migration
    * Fixed toWorldCoordinates bug in moveTo (thanks @xix-xeaon)
    * Added new tests for 2D drawing functions
    * Integrated Coveralls.io, with a badge in README.md
    * Integrated version badge in README.md
    
v0.2.0 (Unreleased)
-----
   * Added license badge in changes.md
   * Fixed Solid.makeSphere implementation
   * Added CQ.sphere operation that mirrors CQ.box
   * Updated copyright dates
   * Cleaned up spelling and misc errors in docstrings
   * Fixed FreeCAD import error on Arch Linux (thanks @moeb)
   * Made FreeCAD import report import error instead of silently failing (thanks @moeb)
   * Added ruled option for the loft operation (thanks @hyOzd)
   * Fixed close() not working in planes other than XY (thanks @hyOzd)
   * Added box selector with bounding box option (thanks @hyOzd)
   * CQ.translate and CQ.rotate documentation fixes (thanks @hyOzd)
   * Fixed centering of a sphere
   * Increased test coverage
