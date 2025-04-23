from setuptools import setup, find_packages

setup(
    name="network_scanner",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        'scapy>=2.4.0',
    ],
    entry_points={
        'console_scripts': [
            'netscan=network_scanner.main:main',
        ],
    },
)
# pip install -e .