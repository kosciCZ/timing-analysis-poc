import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="tapoc",
    version="0.0.1",
    author="Jan Koscielniak",
    author_email="jkosci@gmail.com",
    description="A small proof-of-concept project to figure out how to perform timing analysis.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kosciCZ/timing-analysis-poc/",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
