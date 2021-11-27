import pathlib

from setuptools import setup, find_packages

here = pathlib.Path(__file__).parent.resolve()

long_description = (here / 'README.md').read_text(encoding='utf-8')

setup(
    name='military_symbol',
    version='1.0.0',
    description='Lightweight library for producing SVGs of NATO standard military symbols from NATO sidcs or natural-language descriptions',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/nwroyer/Python-Military-Symbols',
    author='Nicholas Royer',
    author_email='nick.w.royer@protonmail.com',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Other Audience',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Topic :: Multimedia :: Graphics',
        'Topic :: Scientific/Engineering :: Visualization',
        'Topic :: Scientific/Engineering :: GIS',
        'Topic :: Utilities'
    ],
    keywords='military,NATO,symbol,APP-6D,MIL-STD-2525D,map',
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    python_requires='>=3.6, <4',
    install_requires=['lxml', 'svgpathtools', ''],
    package_data={  # Optional
        'military_symbol': ['symbols.json'],
    },
    entry_points= {
        'console_scripts': [
            'military_symbol=military_symbol.command_line:main'
        ]
    }
)