# Copyright 2015 Parametric Products Intellectual Holdings, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
from setuptools import setup, find_packages

reqs = []
setup_reqs = []

# ReadTheDocs, AppVeyor and Azure builds will break when trying to instal pip deps in a conda env
is_rtd = "READTHEDOCS" in os.environ
is_appveyor = "APPVEYOR" in os.environ
is_azure = "CONDA_PY" in os.environ
is_conda = "CONDA_PREFIX_1" in os.environ

# Only include the installation dependencies if we are not running on RTD or AppVeyor or in a conda env
if not is_rtd and not is_appveyor and not is_azure and not is_conda:
    reqs = [
        "cadquery-ocp>=7.7.0a0,<7.8",
        "ezdxf",
        "multimethod>=1.7,<2.0",
        "nlopt",
        "nptyping==2.0.1",
        "typish",
        "casadi",
        "path",
    ]

    setup_reqs = ["setuptools_scm"]

setup(
    name="cadquery",
    # use_scm_version=True,
    version="2.2.0",
    url="https://github.com/CadQuery/cadquery",
    license="Apache Public License 2.0",
    author="David Cowden",
    author_email="dave.cowden@gmail.com",
    description="CadQuery is a parametric  scripting language for creating and traversing CAD models",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=("tests",)),
    python_requires=">=3.8,<3.11",
    setup_requires=setup_reqs,
    install_requires=reqs,
    extras_require={
        "dev": ["docutils", "ipython", "pytest", "black==19.10b0", "click==8.0.4",],
        "ipython": ["ipython",],
    },
    include_package_data=True,
    zip_safe=False,
    platforms="any",
    test_suite="tests",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        #'Development Status :: 6 - Mature',
        #'Development Status :: 7 - Inactive',
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: POSIX",
        "Operating System :: MacOS",
        "Operating System :: Unix",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet",
        "Topic :: Scientific/Engineering",
    ],
)
