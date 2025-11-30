from setuptools import setup, find_packages

setup(
    name="InstanceTracker",
    version="0.1.0",
    description="A metaclass for tracking object instances with weakref and context managers",
    author="ShirinST",
    author_email="e.v.shirinst@outlook.com",
    url="https://github.com/shirinst/InstanceTracker",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
