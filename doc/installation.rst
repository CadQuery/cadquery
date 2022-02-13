.. _installation:

Installing CadQuery
===================================

CadQuery 2 is based on
`OCP <https://github.com/CadQuery/OCP>`_,
which is a set of Python bindings for the open-source `OpenCascade <http://www.opencascade.com/>`_ modelling kernel.

Conda
----------------------------------------------
In principle any conda distrubtion will work, but it is probably best to install `Miniforge <https://github.com/conda-forge/miniforge>`_ to a local directory and to avoid running `conda init`. After performing a local directory installation, Miniforge can be activated via the [scripts,bin]/activate scripts. This will help avoid polluting and breaking the local Python installation. In Linux/MacOS, the local directory installation method looks something like this::

        # Install the script to ~/miniforge
        wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh -O miniforge.sh
        bash miniforge.sh -b -p $HOME/miniforge

        # To activate and use Miniconda
        source $HOME/miniforge/bin/activate

On Windows one can install locally as follows::

        :: Install
        curl -L -o miniforge.exe https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Windows-x86_64.exe
        start /wait "" miniforge.exe /InstallationType=JustMe /RegisterPython=0 /NoRegistry=1 /NoScripts=1 /S /D=%USERPROFILE%\Miniforge3

        :: Activate
        cmd /K ""%USERPROFILE%/Miniforge3/Scripts/activate.bat" "%USERPROFILE%/Miniforge3""

It might be worthwhile to consider using ``/NoScripts=0`` to have an activation shortcut added to the start menu.

Command Line Installation
------------------------------------------

CadQuery development moves very quickly, so you will need to choose whether you want the latest features or an older, probably more stable, version of CadQuery.

To get the latest features (recommended), once you have Anaconda or Miniconda installed, activate the `conda environment <https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html>`_ you want to use and type::

        conda install -c cadquery -c conda-forge cadquery=master

If you want an older, more stable version of CadQuery, once you have Anaconda or Miniconda installed, activate the `conda environment <https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html>`_ you want to use and type::

        conda install -c conda-forge -c cadquery cadquery=2

Test Your Installation
------------------------

If all has gone well, you can open a command line/prompt, and type::

      $ python
      $ import cadquery
      $ cadquery.Workplane('XY').box(1,2,3).toSvg()

You should see raw SVG output displayed on the command line if the CadQuery installation was successful.

Adding a Nicer GUI via CQ-editor
--------------------------------------------------------

If you prefer to have a GUI available, your best option is to use
`CQ-editor <https://github.com/CadQuery/CQ-editor>`_.

CQ-editor relies on Anaconda/Miniconda as well, and the README explains how to set up an environment that will run CQ-editor. However, if you are running the master branch (latest features) of CadQuery, you will want to install CQ-editor into your activated Anaconda environment with the following::

        conda install -c cadquery -c conda-forge cq-editor=master


