# -*- coding: utf-8 -*-
from setuptools import setup
import os

from setuptools import setup, find_packages

from expipe.version import version

long_description = open("README.md").read()

entry_points = None

# install_requires = ['numpy>=1.9.0',
#                     'quantities>=0.9.0',
#                     'neo>=0.4.0.dev0',
#                     'scipy',
#                     'matplotlib>=1.1.0',
#                     'pandas',
#                     'pywavelets',
#                     ]

install_requires = []

setup(name="expipe",
      version=version,
      packages=find_packages(),
      entry_points=entry_points,
      include_package_data=True,
      install_requires=install_requires,
      requires=['OpenElectrophy','pycircstat','astropy',],
      author="CINPLA",
      author_email="",
      maintainer="Mikkel Elle Lepperød",
      maintainer_email="m.e.lepperod@medisin.uio.no",
      long_description=long_description,
      url="https://github.com/CINPLA/expipe",
      platforms=['Linux', "Windows"],
      license="BSD",
      description="",
      classifiers=['Development Status :: Alpha',
                   'Intended Audience :: Science/Research',
                   'License :: OSI Approved :: GPLv2 License',
                   'Natural Language :: English',
                   'Programming Language :: Python :: 2',
                   'Topic :: Scientific/Engineering :: Bio-Informatics'
                   ],
      )
