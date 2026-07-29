from setuptools import setup, find_packages

setup(
    name='chromadb_desktop',
    version='0.1.0',
    description='Small desktop wrapper around ChromaDB and sentence-transformers',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    include_package_data=True,
    install_requires=[
        # keep minimal here; CI/install uses requirements.txt
    ],
)
