# cadquery

[![Travis Build Status](https://api.travis-ci.org/adam-urbanczyk/cadquery.svg?branch=cq1_pythonocc)](https://api.travis-ci.org/adam-urbanczyk/cadquery?branch=cq1_pythonocc)
[![Appveyor Build status](https://ci.appveyor.com/api/projects/status/ub6t3qrjj5h7g1vp/branch/cq1_pythonocc?svg=true)](https://ci.appveyor.com/project/adam-urbanczyk/cadquery/branch/cq1_pythonocc)

This is an experimental CadQuery fork that uses PythonOCC instead of FreeCAD. It also has preliminary Jupyter notebook integration.

This fork of the base repo has changes which support use by [cqparts](https://github.com/CapableRobot/cqparts).

## Linux Installation

You can try it out using conda

```
conda install -c pythonocc -c oce -c conda-forge -c dlr-sc -c CadQuery cadquery-occ
```

## MacOS Installation

Binary builds are not currently available, so you'll need to install pythonocc and then build this library.

```
conda install -c conda-forge -c dlr-sc -c pythonocc -c oce pythonocc-core python=3.6
git clone https://github.com/CapableRobot/cadquery
cd cadquery
python3 setup.py install
```


