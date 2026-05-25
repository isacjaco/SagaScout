"""Setup configuration for SagaScout."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="sagascout",
    version="0.1.0",
    author="isacjaco",
    description="Autonomous Lineage Intelligence for DNA, Genealogy, and Global Discovery",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/isacjaco/SagaScout",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "networkx>=2.6",
        "requests>=2.28.0",
        "beautifulsoup4>=4.11.0",
        "deep-translator>=1.11.0",
        "python-gedcom>=1.0.0",
        "fastapi>=0.100.0",
        "uvicorn>=0.20.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
        ],
        "api": [
            "fastapi>=0.100.0",
            "uvicorn>=0.20.0",
            "httpx>=0.24.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "sagascout=sagascout.__main__:main",
        ],
    },
)
