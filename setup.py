from setuptools import setup, find_packages

try:
    with open("README.md") as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = "<README.md not found>"


def _get_version():
    try:
        with open("VERSION") as vfp:
            return vfp.read().strip()
    except FileNotFoundError:
        return "Unknown"


setup(
    name="soulstruct-gui",
    version=_get_version(),
    packages=find_packages(),
    description="GUI and console tools for FromSoftware mod projects.",
    long_description=long_description,
    install_requires=["colorama", "psutil", "soulstruct"],
    extras_require={
        "Interactive": ["IPython"],
        "Translate": ["googletrans>=3.1.0a0"],
    },
    author="Scott Mooney (Grimrukh)",
    author_email="grimrukh@gmail.com",
    url="https://github.com/Grimrukh/soulstruct-gui",
)
