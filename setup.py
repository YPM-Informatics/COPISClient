import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='COPIS',
    version='0.1.0',
    author='Songie Park',
    author_email='songie.park@yale.edu',
    url='https://github.com/parksong22/COPIS',
    license='LICENSE.txt',
    description='Computer-Orperated Photogrammetric Imaging System package',
    long_description=open('README.txt').read(),
    packages=setuptools.find_packages(),
    install_requires=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)