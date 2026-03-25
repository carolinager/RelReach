from setuptools import setup, find_packages

setup(
    name='relreach',
    version='1.0',
    description='Model checker for Relational Properties',
    author='Lina Gerlach',
    author_email='gerlach@cs.rwth-aachen.com',
    packages=find_packages(),
    install_requires=[
        'termcolor',
        'stormpy @ git+https://github.com/carolinager/stormpy.git@relprop#egg=stormpy',
        'pycarl==2.3.0',
    ],
)
