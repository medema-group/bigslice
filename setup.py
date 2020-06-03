import setuptools

setuptools.setup(
    name="bigslice",
    version="1.0.0",
    scripts=[
        "bigslice/bigslice",
        "bigslice/db/download_bigslice_hmmdb.py"
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
    python_requires='>=3.6',
    install_requires=[
        "numpy",
        "pandas",
        "biopython >= 1.69",
        "scikit-learn",
        "pysqlite3"
    ]
)
