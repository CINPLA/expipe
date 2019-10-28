# -*- coding: utf-8 -*-
from setuptools import setup
import os

from setuptools import setup, find_packages

long_description = open("README.md").read()

with open("requirements.txt", mode='r') as f:
    install_requires = f.read().split('\n')

install_requires = [e for e in install_requires if len(e) > 0]

d = {}
exec(open("expipe/version.py").read(), None, d)
version = d['version']
pkg_name = "expipe"

setup(name="expipe",
      packages=find_packages(),
      version=version,
      include_package_data=True,
      author="CINPLA",
      author_email="",
      maintainer="Mikkel Elle Lepperød",
      maintainer_email="m.e.lepperod@medisin.uio.no",
      long_description=long_description,
      url="https://github.com/CINPLA/expipe",
      platforms=['Linux', "Windows"],
      install_requires=install_requires,
      description="Experiment-data management platform",
      classifiers=['Intended Audience :: Science/Research',
                   'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
                   'Natural Language :: English',
                   'Programming Language :: Python :: 3',
                   'Topic :: Scientific/Engineering'
                   ],
      )
