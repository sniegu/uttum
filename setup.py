from setuptools import setup

## afdg

setup(
    name='uttum',
    version='0.1',
    packages=['uttum'],
    entry_points = {
        'console_scripts': [
            'uttum = uttum.cli:run',
        ],
    },
    zip_safe=True,
)
