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
from setuptools import setup


#if we are building in travis, use the build number as the sub-minor version
version = '1.1.0'
if 'TRAVIS_TAG' in list(os.environ.keys()):
    version= os.environ['TRAVIS_TAG']


setup(
    name='cadquery',
    version=version,
    url='https://github.com/dcowden/cadquery',
    license='Apache Public License 2.0',
    author='David Cowden',
    author_email='dave.cowden@gmail.com',
    description='CadQuery is a parametric  scripting language for creating and traversing CAD models',
    long_description=open('README.md').read(),
    packages=['cadquery','cadquery.contrib','cadquery.freecad_impl','cadquery.plugins','tests'],
    install_requires=['pyparsing'],
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    test_suite='tests',

    classifiers=[
        'Development Status :: 5 - Production/Stable',
        #'Development Status :: 6 - Mature',
        #'Development Status :: 7 - Inactive',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Science/Research',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX',
        'Operating System :: MacOS',
        'Operating System :: Unix',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Internet',
        'Topic :: Scientific/Engineering'
    ]
)
