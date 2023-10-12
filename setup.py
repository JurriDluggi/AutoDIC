#!/usr/bin/env python

from distutils.core import setup
import py2exe
import glob
import os,sys

lib_dir = os.path.abspath("./lib")
sys.path.append(lib_dir)

setup(name='AutoDIC',
      version='1.0.0',
      description='Automatic FIB-DIC acquisition via SharkSEM',
      author='Jiri Dluhos',
      author_email='jiri.dluhos@tescan.cz',
      description="TESCAN iStress FIB-DIC Acquisition",
      download_url='https://gitlab.com/istress/AutoDIC.git',
      install_requires=['PySide', 'scipy','numpy', 'PIL','skimage'],
      classifiers=[
          'Development Status :: Beta',
          'Environment :: Qt',
          'Intended Audience :: Developers',
          'Operating System :: Microsoft :: Windows',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.2',
          'Programming Language :: Python :: 3.3',
          'Programming Language :: Python :: 3.4',
          ],
      packages=['AutoDIC'],
      console=['AutoDIC.py'],
      zipfile=None, 
      package_data={ 'AutoDIC': ["images/*","geometries/*"],
          },
        
      options = {
                  'py2exe': {
                      'includes': 'DIC_lib',
                  }
              },
     )
     
