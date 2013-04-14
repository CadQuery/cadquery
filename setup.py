setup(
    name='cadquery',
    version=get_version(),
    url='https://github.com/dcowden/cadquery',
    license='LGPL',
    author='David Cowden',
    author_email='dave.cowden@gmail.com',
    description='CadQuery is a parametric  scripting language for creating and traversing CAD models',
    long_description=__doc__,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=['FreeCAD'], #how to list FreeCAD here?
    #entry_points='''\
    #[console_scripts]
    ##rqworker = rq.scripts.rqworker:main
    #rqinfo = rq.scripts.rqinfo:main
    #''',
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
        'License :: OSI Approved :: LGPL License',
        'Operating System :: POSIX',
        'Operating System :: MacOS',
        'Operating System :: Unix',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Internet',
        'Topic :: Scientific/Engineering'
    ]
)