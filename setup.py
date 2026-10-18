from setuptools import setup, find_packages

setup(
    name="archclean",
    version="0.1.0",
    packages=find_packages(),
    entry_points={"console_scripts": ["archclean=archclean.main:main"]},
    install_requires=["PyGObject"],
)
