# Readme

This is a script for generating a self installer for cadquery using conda constructor

  * https://github.com/conda/constructor

The installer

  * Installs an instance of miniconda
  * Adds cadquery / conda-forge to the default channels
  * Runs a post install script to download install cadquery.

We need to install cadquery post install due to the file sizes involved with the install of opencascade (around 2Gb)
This installer will not add the installed directory to the Path or try to override the default python (with the default options selected).

To run
```
build.py <installer version> <github tag version>
```
