#!/usr/bin/env python2.7
"""
Install script for mrboterson

micha gorelick, mynameisfiber@gmail.com
http://micha.codes/
"""

from setuptools import setup

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='mrboterson',
    version='0.2.0',
    description='quick and easy async slack bot library',
    author='Micha Gorelick',
    author_email='mynameisfiber@gmail.com',
    url='http://github.com/mynameisfiber/mrboterson/',
    download_url='https://github.com/mynameisfiber/mrboterson/tarball/master',
    license="GNU Lesser General Public License v3 or later (LGPLv3+)",
    classifiers=[
        "Programming Language :: Python",
        "Topic :: Communications :: Chat",
        "Framework :: Robot Framework",
        "Topic :: Software Development :: Libraries",
        "License :: OSI Approved :: GNU Lesser General "
                "Public License v3 or later (LGPLv3+)",
    ],
    packages=['mrboterson', 'mrboterson.lib', 'mrboterson.plugins'],
    install_requires=requirements,
)
