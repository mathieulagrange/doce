from setuptools import setup, find_packages
import sys

from importlib.machinery import SourceFileLoader

version = SourceFileLoader('doce.version',
                           'doce/version.py').load_module()

with open('README.md', 'r') as fdesc:
    long_description = fdesc.read()

setup(
    name='doce',
    version=version.version,
    description='Design of computational experiments',
    author='Mathieu Lagrange',
    author_email='mathieu.lagrange@ls2n.fr',
    url='https://mathieulagrange.github.io',
    download_url='https://github.com/mathieulagrange/doce',
    packages=find_packages(),
    long_description=long_description,
    long_description_content_type='text/markdown',
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    keywords='experimentation',
    license='ASL',
    install_requires=[
        'tables',
        'pandas',
        'argunparse',
        'numpy',
        'tqdm',
        'joblib',
    ],
    python_requires='>=3.6',
    extras_require={
        'docs': ['numpydoc', 'sphinx'],
    }
)
