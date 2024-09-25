from setuptools import setup, find_packages
import sys

# if sys.version_info[0] == 2:
#     sys.exit('Sorry, Python 2.x is not supported')

setup(
    name='relreach',
    version='0.0',
    description='Model checker for Relational Reachability Properties',
    author='Lina Gerlach',
    author_email='gerlach@cs.rwth-aachen.com',
    packages=find_packages(),
    install_requires=[
        'stormpy>=1.6.3',
        'lark-parser',
        'z3-solver==4.11.2',
        'termcolor'
    ],
    # python_requires='>=3.9',

    # classifiers=[
    #     'Environment :: MacOS X',
    #     'Intended Audience :: Science/Research',
    #     'License :: OSI Approved :: MIT License',
    #     'Operating System :: MacOS :: MacOS X',
    #     'Operating System :: MacOS :: MacOS X',
    #     'Programming Language :: Python :: 3.9',
    #     'Topic :: Scientific/Engineering',
    #     'Topic :: Software Development :: Libraries :: Python Modules'
    # ],
)
