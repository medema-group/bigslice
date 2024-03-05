import setuptools

setuptools.setup(
    name="bigslice",
    version="2.0",
    scripts=[
        "bigslice/bigslice",
        "bigslice/download_bigslice_hmmdb",
        "bigslice/vectorize_bgcs"
    ],
    author="Satria A. Kautsar",
    author_email="satriaphd@gmail.com",
    description=("A highly scalable, user-interactive tool"
                 " for the large scale analysis of"
                 " Biosynthetic Gene Clusters data"),
    long_description=(
        "Please see our GitHub page: "
        "https://github.com/medema-group/bigslice"
    ),
    url="https://github.com/satriaphd/bigslice",
    packages=setuptools.find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3"
    ],
    python_requires='>=3.7',
    install_requires=[
        "pyhmmer",
        "biopython>=1.73,<=1.83",
        "numpy",
        "pandas",
        "scikit-learn",
        "tqdm",
        "pyarrow"
    ]
)
