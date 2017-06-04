# -*- coding: utf-8 -*-
from setuptools import setup
import os

from setuptools import setup, find_packages
import versioneer

long_description = open("README.md").read()

install_requires = ['pyrebase', 'quantities']

setup(name="expipe",
      packages=find_packages(),
      version=versioneer.get_version(),
      cmdclass=versioneer.get_cmdclass(),
      include_package_data=True,
      author="CINPLA",
      author_email="",
      maintainer="Mikkel Elle Lepperød",
      maintainer_email="m.e.lepperod@medisin.uio.no",
      long_description=long_description,
      url="https://github.com/CINPLA/expipe",
      platforms=['Linux', "Windows"],
      description="",
      classifiers=['Development Status :: Alpha',
                   'Intended Audience :: Science/Research',
                   'License :: OSI Approved :: GPLv2 License',
                   'Natural Language :: English',
                   'Programming Language :: Python :: 2',
                   'Topic :: Scientific/Engineering :: Bio-Informatics'
                   ],
      )
