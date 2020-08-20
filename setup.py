import ast
import os
import re

from setuptools import find_packages, setup

_version_re = re.compile(r"__version__\s+=\s+(.*)")
_root = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(_root, "sea/__init__.py")) as f:
    version = str(ast.literal_eval(_version_re.search(f.read()).group(1)))

with open(os.path.join(_root, "requirements.txt")) as f:
    requirements = f.readlines()

with open(os.path.join(_root, "README.md")) as f:
    readme = f.read()


def find_package_data(package):
    """
    Return all files under the root package, that are not in a
    package themselves.
    """
    walk = [
        (dirpath.replace(package + os.sep, "", 1), filenames)
        for dirpath, dirnames, filenames in os.walk(package)
    ]

    filepaths = []
    for base, filenames in walk:
        filepaths.extend([os.path.join(base, filename) for filename in filenames])
    return filepaths


setup(
    name="sea",
    version=version,
    description="rpc framework",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="https://github.com/balletcrypto/sea",
    author="Michael Ding",
    author_email="yandy.ding@gmail.com",
    license="MIT",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "Operating System :: POSIX",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Internet",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords=["rpc", "grpc"],
    packages=find_packages(exclude=["tests"]),
    package_data={"sea": find_package_data("sea")},
    python_requires=">=3.7",
    install_requires=requirements,
    entry_points={"console_scripts": ["sea=sea.cli:main"]},
)
