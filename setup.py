from setuptools import setup

setup(name='wradvis',
      version='0.1.0',
      packages=['wradvis'],
      entry_points={
          'gui_scripts': [
              'wradvis = wradvis.gui:start'
          ]
      },
      )
