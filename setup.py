# -*- coding: utf-8 -*-
__author__ = 'jb'


from distutils.core import setup

setup(name='Django migration manager',
      version='1.1',
      description='A simple manager for migrations stored as plain SQL files',
      author='Jacek Bzdak',
      author_email='jbzdak@gmail.com',
      packages=['migration_manager'],
      requires=[
          'django(>=1.0)', #Well tests uses settings changing. Otherwise you might use any recent version.
      ],
      classifiers=[
            "Development Status :: 3 - Alpha",
            "Environment :: Web Environment",
            "Framework :: Django",
            "Operating System :: OS Independent",
            "Intended Audience :: Developers",
            "License :: Public Domain",
            "Programming Language :: Python",
        ],
      long_description= open("README.txt").read()
)
