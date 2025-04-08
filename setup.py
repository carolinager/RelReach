from setuptools import setup, find_packages
import importlib.util
import sys

# if sys.version_info[0] == 2:
#     sys.exit('Sorry, Python 2.x is not supported')

setup(
    name='relreach',
    version='1.0',
    description='Model checker for Relational Reachability Properties',
    author='Lina Gerlach',
    author_email='gerlach@cs.rwth-aachen.com',
    packages=find_packages(),
    install_requires=[
        'termcolor',
        'stormpy @ git+https://github.com/carolinager/stormpy.git@relreach-full#egg=stormpy', 
        'pycarl==2.3.0',
    ],

    # todo
    # python_requires='>=3.9',
    # classifiers=[
    #     'Intended Audience :: Science/Research',
    #     'License :: OSI Approved :: MIT License',
    #     'Programming Language :: Python :: 3.9',
    #     'Topic :: Scientific/Engineering',
    #     'Topic :: Software Development :: Libraries :: Python Modules'
    # ],
)
