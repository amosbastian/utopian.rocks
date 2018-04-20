from setuptools import find_packages, setup

setup(
    author="Amos Bastian",
    author_email="amosbastian@googlemail.com",
    license="MIT",
    name="utopian",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "pymongo",
        "requests"
    ]
)