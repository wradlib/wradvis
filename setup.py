#!/usr/bin/env python
# Copyright (c) 2016-2018, wradlib developers.
# Distributed under the MIT License. See LICENSE.txt for more info.


def setup_package():

    from setuptools import setup, find_packages

    metadata = dict(
        name='wradvis',
        version='0.1.0',
        packages=find_packages(),
        entry_points={
            'gui_scripts': [
                'wradvis = wradvis.gui:start'
              ]
          },
    )

    setup(**metadata)


if __name__ == '__main__':
    setup_package()
