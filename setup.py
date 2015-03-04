from setuptools import setup

setup(
    name='cadquery',
    version='0.1.8',
    url='https://github.com/dcowden/cadquery',
    license='LGPL',
    author='David Cowden',
    author_email='dave.cowden@gmail.com',
    description='CadQuery is a parametric  scripting language for creating and traversing CAD models',
    long_description=open('README.txt').read(),
    packages=['cadquery','cadquery.contrib','cadquery.freecad_impl','cadquery.plugins','tests'],
    include_package_data=True,
    zip_safe=False,
    platforms='any',

    classifiers=[
        # As from http://pypi.python.org/pypi?%3Aaction=list_classifiers
        #'Development Status :: 1 - Planning',
        #'Development Status :: 2 - Pre-Alpha',
        'Development Status :: 3 - Alpha',
        #'Development Status :: 4 - Beta',
        #'Development Status :: 5 - Production/Stable',
        #'Development Status :: 6 - Mature',
        #'Development Status :: 7 - Inactive',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Science/Research',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
        'Operating System :: POSIX',
        'Operating System :: MacOS',
        'Operating System :: Unix',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Internet',
        'Topic :: Scientific/Engineering'
    ]
)
