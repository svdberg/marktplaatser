#!/usr/bin/env python3
"""Setup script for marktplaats-backend package."""

from setuptools import setup, find_packages

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="marktplaats-backend",
    version="1.0.0",
    author="Marktplaatser Team",
    description="AWS Lambda application for generating marketplace listings from images",
    long_description="""
    This package processes uploaded images through AWS Rekognition for object detection and text extraction,
    then uses AWS Bedrock to generate structured listing data that matches Marktplaats categories and attributes.
    """,
    long_description_content_type="text/plain",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "black>=22.0",
            "flake8>=5.0",
            "mypy>=1.0",
        ],
        "test": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
        ],
    },
)