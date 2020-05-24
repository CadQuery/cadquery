![CadQuery logo](./doc/_static/logo/cadquery_logo_dark.svg)
# CadQuery

[![Travis Build Status](https://travis-ci.org/CadQuery/cadquery.svg?branch=master)](https://travis-ci.org/CadQuery/cadquery.svg?branch=master)
[![Appveyor Build status](https://ci.appveyor.com/api/projects/status/cf4qg6kpyqmcje1h?svg=true)](https://ci.appveyor.com/api/projects/status/cf4qg6kpyqmcje1h?svg=true)
[![Build Status](https://dev.azure.com/cadquery/conda-packages/_apis/build/status/CadQuery.cadquery?branchName=master)](https://dev.azure.com/cadquery/conda-packages/_build/latest?definitionId=2&branchName=master)
[![codecov](https://codecov.io/gh/CadQuery/cadquery/branch/master/graph/badge.svg)](https://codecov.io/gh/CadQuery/cadquery)
[![Documentation Status](https://readthedocs.org/projects/cadquery/badge/?version=latest)](https://cadquery.readthedocs.io/en/latest/?badge=latest)

## What is CadQuery

CadQuery is an intuitive, easy-to-use Python module for building parametric 3D CAD models. Using CadQuery, you can write short, simple scripts that produce high quality CAD models. It is easy to make many different objects using a single script that can be customized.

CadQuery is often compared to [OpenSCAD](http://www.openscad.org/). Like OpenSCAD, CadQuery is an open-source, script based, parametric model generator. However, CadQuery stands out in many ways and has several key advantages:

1. The scripts use a standard programming language, Python, and thus can benefit from the associated infrastructure. This includes many standard libraries and IDEs.
2. CadQuery's CAD kernel Open CASCADE Technology (OCCT) is much more powerful than CGAL. Features supported natively by OCCT include NURBS, splines, surface sewing, STL repair, STEP import/export, and other complex operations, in addition to the standard CSG operations supported by CGAL
3. Ability to import/export STEP and the ability to begin with a STEP model, created in a CAD package, and then add parametric features. This is possible in OpenSCAD using STL, but STL is a lossy format.
4. CadQuery scripts require less code to create most objects, because it is possible to locate features based on the position of other features, workplanes, vertices, etc.
5. CadQuery scripts can build STL, STEP, and AMF faster than OpenSCAD.

### Key features
* Build 3D models with scripts that are as close as possible to how you would describe the object to a human.
* Create parametric models that can be very easily customized by end users.
* Output high quality (loss-less) CAD formats like STEP in addition to STL and AMF.
* Provide a non-proprietary, plain text model format that can be edited and executed with only a web browser.
* Offer advanced modeling capabilities such as fillets, curvelinear extrudes, parametric curves and lofts.

### Why this fork

The original version of CadQuery was built on the FreeCAD API. This was great because it allowed for fast development and easy cross-platform capability. However, we eventually started reaching the limits of the API for some advanced operations and selectors. This 2.0 version of CadQuery is based directly on a Python wrapper of the OCCT kernel. This gives us a great deal more control and flexibility, at the expense of some simplicity and having to handle the cross-platform aspects of deployment ourselves. We believe this is a worthwhile trade-off to allow CadQuery to continue to grow and expand in the future.

## Getting started

It is currently possible to use CadQuery for your own projects in 3 different ways:
* Using the [CQ-editor GUI](https://github.com/CadQuery/CQ-editor)
* From a [Jupyter notebook](https://github.com/bernhard-42/jupyter-cadquery)
* As a standalone library

The easiest way to install CadQuery and its dependencies is using conda:
```
conda install -c conda-forge -c cadquery cadquery=2
```
Development version can be installed as well:
```
conda install -c conda-forge -c cadquery cadquery=master
```

For those who are interested, the [OCP repository](https://github.com/CadQuery/OCP) contains the current OCCT wrapper used by CQ.

### CQ-editor GUI

CQ-editor is an IDE that allows users to edit CadQuery model scripts in a GUI environment. It includes features such as:

* A graphical debugger that allows you to step through your scripts.
* A CadQuery stack inspector.
* Export to various formats, including STEP and STL, directly from the menu.

The installation instructions for CQ-editor can be found [here](https://github.com/CadQuery/CQ-editor#installation).

<img src="https://raw.githubusercontent.com/CadQuery/CQ-editor/master/screenshots/screenshot3.png" alt="CQ editor screenshot" width="800"/>

### Jupyter

CadQuery supports Jupyter notebook out of the box using the jupyter-cadquery extension created by @bernhard-42:

* [Installation](https://github.com/bernhard-42/jupyter-cadquery#installation)
* [Usage](https://github.com/bernhard-42/jupyter-cadquery#jupyter-cadquery)

<img src="https://raw.githubusercontent.com/bernhard-42/jupyter-cadquery/master/screenshots/0_intro.png" alt="CadQuery Jupyter extension screenshot" width="800"/>

### Standalone

CadQuery was built to be used as a Python library without any GUI. This makes it great for use cases such as integration into servers, or creating scientific and engineering scripts. Use Anaconda/Miniconda to install CadQuery, and then add `import cadquery` to the top of your Python scripts.

```
conda install -c conda-forge -c cadquery cadquery=2
```

## Getting help

You can find the full CadQuery documentation at [cadquery.readthedocs.io](https://cadquery.readthedocs.io/).

We also have a [Google Group](https://groups.google.com/forum/#!forum/cadquery) to make it easy to get help from other CadQuery users. We want you to feel welcome and encourage you to join the group and introduce yourself. We would also love to hear what you are doing with CadQuery.

## Projects using CadQuery

Here are just a few examples of how CadQuery is being used.

### Resin Mold for Cable Repair 

Thanks to @hyOzd ( Altu Technology ) for this example.

![Resin mold example](https://camo.githubusercontent.com/3dcbe1b644b4b831d88e323ab5414a392d7feef0/687474703a2f2f64636f7764656e2e6769746875622e696f2f63616471756572792f5f7374617469632f68794f7a642d6361626c656669782e706e67) ![Resin mold being machined](http://dcowden.github.io/cadquery/_static/hyOzd-finished_thumb.jpg)

### Generation of KiCAD Component Files

Thanks to @easyw for this example from the [kicad-3d-models-in-freecad project](https://github.com/easyw/kicad-3d-models-in-freecad).

<img src="http://dcowden.github.io/cadquery/_static/KiCad_Capacitors_SMD.jpg" alt="Circuit board generated in KiCAD" width="400"/>

### 3D Printed Resin Mold

Thanks to @eddieliberato for this example.

<img src="https://user-images.githubusercontent.com/13981538/55984103-f7968080-5c9c-11e9-94ef-b02b28be4432.png" alt="3D printed resin mold" height="250"/> <img src="https://user-images.githubusercontent.com/13981538/55984149-1ac13000-5c9d-11e9-9825-c0aadbadd280.png" alt="3D printed resin mold" height="250"/>

## License

CadQuery is licensed under the terms of the [Apache Public License, version 2.0](http://www.apache.org/licenses/LICENSE-2.0).

## Contributing

Contributions from the community are welcome and appreciated.

You do not need to be a software developer to have a big impact on this project. Contributions can take many forms including, but not limited to, the following:

* Writing and improving documentation
* Triaging bugs
* Submitting bugs and feature requests
* Creating tutorial videos and blog posts
* Helping other users get started and solve problems
* Telling others about this project
* Helping with translations and internationalization
* Helping with accessibility
* Contributing bug fixes and new features

It is asked that all contributions to this project be made in a respectful and considerate way. Please use the [Python Community Code of Conduct's](https://www.python.org/psf/codeofconduct/) guidelines as a reference.

### Contributing code

If you are going to contribute code, make sure to follow this steps:

- Consider opening an issue first to discuss what you have in mind
- Try to keep it as short and simple as possible (if you want to change several
  things, start with just one!)
- Fork the CadQuery repository, clone your fork and create a new branch to
  start working on your changes
- Start with the tests! How should CadQuery behave after your changes? Make
  sure to add some tests to the test suite to ensure proper behavior
- Make sure your tests have assertions checking all the expected results
- Add a nice docstring to the test indicating what the test is doing; if there
  is too much to explain, consider splitting the test in two!
- Go ahead and implement the changes
- Add a nice docstring to the functions/methods/classes you implement
  describing what they do, what the expected parameters are and what it returns
  (if anything)
- Update the documentation if there is any change to the public API
- Consider adding an example to the documentation showing your cool new
  feature!
- Make sure nothing is broken (run the complete test suite with `pytest`)
- Run `black` to autoformat your code and make sure your code style complies
  with CadQuery's
- Push the changes to your fork and open a pull-request upstream
- Keep an eye on the automated feedback you will receive from the CI pipelines;
  if there is a test failing or some code is not properly formatted, you will
  be notified without human intervention
- Be prepared for constructive feedback and criticism!
- Be patient and respectful, remember that those reviewing your code are also
  working hard (sometimes reviewing changes is harder than implementing them!)

### How to Report a Bug
When filing a bug report [issue](https://github.com/CadQuery/cadquery/issues), please be sure to answer these questions:

1. What version of the software are you running?
2. What operating system are you running the software on?
3. What are the steps to reproduce the bug?

### How to Suggest a Feature or Enhancement

If you find yourself wishing for a feature that does not exist, you are probably not alone. There are bound to be others out there with similar needs. Open an [issue](https://github.com/CadQuery/cadquery/issues) which describes the feature you would like to see, why you need it, and how it should work.
