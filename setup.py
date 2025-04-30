#!/usr/bin/env python
from setuptools import setup

if __name__ == "__main__":
    try:
        setup(name="cloudproxy")
    except:  # noqa
        print(
            "An error occurred during setup; please ensure that setuptools is installed."
        )
        raise 