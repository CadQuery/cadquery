.. _installation:


Installing CadQuery
===================

To install both Cadquery and CQ-Editor together with a single installer see the instructions below `Adding a Nicer GUI via CQ-editor`_.

CadQuery may be installed with either conda or pip.  The conda installation method is the better tested and more mature option.


Install via conda
------------------

Begin by installing the conda package manager.  If conda is already installed skip to `conda`_.


Install the Conda Package Manager
``````````````````````````````````

In principle, any Conda distribution will work, but it is probably best to install `Mambaforge <https://github.com/conda-forge/miniforge#mambaforge>`_ to a local directory and to avoid running `conda init`. After performing a local directory installation, Mambaforge can be activated via the [scripts,bin]/activate scripts. This will help avoid polluting and breaking the local Python installation.

Mambaforge is a minimal installer that sets *conda-forge* as the default channel for package installation and provides **mamba**.   ``mamba install`` is recommended over ``conda install`` for faster and less memory intensive caduqery installation.

In Linux/MacOS, the local directory installation method looks something like this::

    # Install to ~/mambaforge
    curl -L -o mambaforge.sh "https://github.com/conda-forge/miniforge/releases/latest/download/Mambaforge-$(uname)-$(uname -m).sh"
    bash mambaforge.sh -b -p $HOME/mambaforge

    # Activate
    source $HOME/mambaforge/bin/activate


On Windows, download the installer and double click it on the file browser or install non-interactively as follows::

    :: Install to %USERPROFILE%\Mambaforge
    curl -L -o mambaforge.exe https://github.com/conda-forge/miniforge/releases/latest/download/Mambaforge-Windows-x86_64.exe
    start /wait "" mambaforge.exe /InstallationType=JustMe /RegisterPython=0 /NoRegistry=1 /NoScripts=1 /S /D=%USERPROFILE%\Mambaforge

    :: Activate
    cmd /K ""%USERPROFILE%/Mambaforge/Scripts/activate.bat" "%USERPROFILE%/Mambaforge""

It might be worthwhile to consider using ``/NoScripts=0`` to have an activation shortcut added to the start menu.

After conda installation, create and activate a new `conda environment <https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html>`_ to prepare for cadquery installation.


conda
`````

Install the latest released version of cadquery::

    conda create -n cq
    conda activate cq
    mamba install cadquery

or install a given version of cadquery [#f1]_::

    conda create -n cq22
    conda activate cq22
    mamba install cadquery=2.2.0 occt=7.7.0

or install the latest dev version::

    conda create -n cqdev
    conda activate cqdev
    mamba install -c cadquery cadquery=master


Add the *conda-forge* channel explicitly to the install command if needed (not using a miniforge based conda distribution).


Install via pip
---------------

CadQuery has a complex set of dependencies including OCP, which is our set of bindings to the OpenCASCADE CAD kernel. OCP is distributed as binary wheels for Linux, MacOS and Windows. However, there are some limitations. Only Python 3.8 through 3.10 are currently supported, and some older Linux distributions such as Ubuntu 18.04 are not supported. If the pip installation method does not work for your system, you can try the conda installation method.

It is highly recommended that a virtual environment is used when installing CadQuery, although it is not strictly required. Installing CadQuery via pip requires an up-to-date version of pip, which can be obtained with the following command line (or a slight variation thereof).::

    python3 -m pip install --upgrade pip

Once a current version of pip is installed, CadQuery can be installed using the following command line.::

    pip install cadquery

It is also possible to install the very latest changes directly from CadQuery's GitHub repository, with the understanding that sometimes breaking changes can occur. To install from the git repository, run the following command line.::

    pip install git+https://github.com/CadQuery/cadquery.git

You should now have a working CadQuery installation, but developers or users who want to use CadQuery with IPython/Jupyter or to set up a developer environment can read the rest of this section.

If you are installing CadQuery to use with IPython/Jupyter, you may want to run the following command line to install the extra dependencies.::

    pip install cadquery[ipython]

If you want to create a developer setup to contribute to CadQuery, the following command line will install all the development dependencies that are needed.::

    pip install cadquery[dev]


Adding a Nicer GUI via CQ-editor
--------------------------------------------------------

If you prefer to have a GUI available, your best option is to use
`CQ-editor <https://github.com/CadQuery/CQ-editor>`_.


You can download the newest build `here`_. Install and run the *run.sh* (Linux/MacOS) or *run.bat* (Windows) script in the root CQ-editor directory. The CQ-editor window should launch.

.. _here: https://github.com/CadQuery/CQ-editor/releases/tag/nightly

Linux/MacOS
```````````

1. Download the installer (.sh script matching OS and platform).

2. Select the script in the file browser and make executable.  Choose **Properties** from the context menu and select **Permissions**, **Allow executing file as a program** (or similar, this step varies depending on OS and window manager).

3. Select the script in the file browser and choose **Run as Program** (or similar).

   Follow the prompts to accept the license and optionally change the installation location.

   The default installation location is ``/home/<username>/cq-editor``.

4. Launch the **run.sh** script from the file brower (again make executable first and then run as program).


To install from command line, download the installer using curl or wget or your favorite program and run the script.::

    curl -LO https://github.com/CadQuery/CQ-editor/releases/download/nightly/CQ-editor-master-Linux-x86_64.sh
    sh CQ-editor-master-Linux-x86_64.sh


To run from command.::

    $HOME/cq-editor/run.sh


Windows
```````

1. Download the installer (.exe) and double click it on the file browser.

   Follow the prompts to accept the license and optionally change the installation location.

   The default installation location is ``C:\Users\<username>\cq-editor``.

2. Launch the **run.bat** script from the file brower (select **Open**).


To run from command line, activate the environment, then run cq-editor::

    C:\Users\<username>\cq-editor\run.bat


Installing extra packages
```````````````````````````

*mamba*, and *pip* are bundled with the CQ-editor installer and available for package installation.

First activate the environment, then call mamba or pip to install additional packages.

On windows.::

    C:\Users\<username>\cq-editor\Scripts\activate
    mamba install <packagename>

On Linux/MacOS. ::

    source $HOME/cq-editor/bin/activate
    mamba install <packagename>


Adding CQ-editor to an Existing Environment
--------------------------------------------

You can install CQ-editor into a conda environment or Python virtual environment using conda (mamba) or pip.

Example cq-editor installation with conda (this installs both cadquery and cq-editor)::

    conda create -n cqdev
    conda activate cqdev
    mamba install -c cadquery cq-editor=master


Example cq-editor installation with pip::

    pip install PyQt5 spyder pyqtgraph logbook
    pip install git+https://github.com/CadQuery/CQ-editor.git


Jupyter
-------

Viewing models in Jupyter is another good option for a GUI.  Models are rendered in the browser.

The cadquery library works out-of-the-box with Jupyter.
First install cadquery, then install JupyterLab_ in the same conda or Python venv.:

conda

    .. code-block::

       mamba install jupyterlab

pip

    .. code-block::

       pip install jupyterlab


Start JupyterLab::

    jupyter lab


JupyterLab will open automatically in your browser.  Create a Notebook to interactively edit/view CadQuery models.

Call ``display`` to show the model.::

    display(<Workplane, Shape, or Assembly object>)


.. _JupyterLab: https://jupyterlab.readthedocs.io/en/stable/getting_started/installation.html


Test Your Installation
------------------------

If all has gone well, you can open a command line/prompt, and type::

      $ python
      $ import cadquery
      $ cadquery.Workplane('XY').box(1,2,3).toSvg()

You should see raw SVG output displayed on the command line if the CadQuery installation was successful.


.. note::

   .. [#f1] Older releases may not be compatible with the latest OCCT version.  In that case, specify the version of the OCCT dependency explicitly.
