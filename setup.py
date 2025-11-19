"""
Setup script for CS2 Input Visualizer
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = [
        line.strip()
        for line in requirements_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="cs2-input-visualizer",
    version="1.0.0",
    author="CS2 Community",
    author_email="",
    description="Real-time input visualization overlay for CS2 demo playback",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/liker0704/cs2-demo-input-viewer",
    packages=find_packages(include=["src", "src.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Games/Entertainment :: First Person Shooters",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Environment :: X11 Applications :: Qt",
    ],
    python_requires=">=3.10,<3.13",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
            "black>=23.7.0",
        ],
        "msgpack": [
            "msgpack>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "cs2-input-viewer=src.main:main",
            "cs2-etl=src.parsers.etl_pipeline:main",
            "cs2-generate-mock=src.parsers.mock_data_generator:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.md", "*.json", "*.txt"],
    },
    zip_safe=False,
    keywords=[
        "cs2",
        "counter-strike",
        "demo",
        "replay",
        "visualization",
        "overlay",
        "input-viewer",
        "gaming",
    ],
    project_urls={
        "Bug Reports": "https://github.com/liker0704/cs2-demo-input-viewer/issues",
        "Source": "https://github.com/liker0704/cs2-demo-input-viewer",
        "Documentation": "https://github.com/liker0704/cs2-demo-input-viewer/tree/main/docs",
    },
)
