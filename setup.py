"""Setup configuration for AETHER package."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="aether-eval",
    version="0.1.0",
    author="AETHER Team",
    author_email="contact@aether-eval.ai",
    description="Comprehensive AI agent evaluation framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/aether",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
        ],
        "docs": [
            "sphinx>=4.0.0",
            "sphinx-rtd-theme>=1.0.0",
        ],
        "viz": [
            "matplotlib>=3.4.0",
            "plotly>=5.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "aether=aether.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "aether": [
            "config/*.yaml",
            "config/*.json",
            "templates/*.json",
        ],
    },
)