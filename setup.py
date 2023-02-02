
from setuptools import setup, find_packages


setup(
    name='neludim',
    packages=find_packages(
        exclude=['notes']
    ),
    entry_points={
        'console_scripts': [
            'neludim=neludim.cli:main'
        ],
    },
)
