# Readme

This is a script for generating a self installer for cadquery using conda constructor

  * https://github.com/conda/constructor

The installer

  * Installs an instance of miniconda
  * Adds cadquery / conda-forge to the default channels
  * Runs a post install script to download install cadquery.

We need to install cadquery post install due to the file sizes involved with the install of opencascade (around 2Gb)
This installer will not add the installed directory to the Path or try to override the default python (with the default options selected).

## Running the constructor

To run
```
conda install jinja2 constructor
python build.py <installer version> <github tag version>
```

For Example
```
build.py 2.2 master
```

## Activation

To Activate the environment
```
# Under Windows
condabin\activate.bat

# Under Linux / MacOS
source ~/cadquery/bin/activate
```

