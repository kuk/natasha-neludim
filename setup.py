
from setuptools import setup


setup(
    name='neludim',
    entry_points={
        'console_scripts': [
            'neludim=neludim.cli:main'
        ],
    },
)
