from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

long_description = (here / 'README.md').read_text(encoding='utf-8')


def get_version(rel_path):
    init_content = (here / rel_path).read_text(encoding='utf-8')
    for line in init_content.split('\n'):
        if line.startswith('__version__'):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    else:
        raise RuntimeError("Unable to find version string.")


setup(
    name='twiget',

    version=get_version("twiget/__init__.py"),

    description='A package for management of filtering queries of the Twitter API',
    long_description=long_description,
    long_description_content_type='text/markdown',

    url='https://github.com/aesuli/twiget',

    author='Andrea Esuli',
    author_email='andrea@esuli.it',

    classifiers=[
        'Development Status :: 4 - Beta',

        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Programming Language :: Python',
        'Topic :: Software Development',
        'Topic :: Scientific/Engineering',

        'License :: OSI Approved :: BSD License',

        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3 :: Only',
    ],

    keywords='twitter, retrieval, streams, tweets, search, filter, API',

    packages=find_packages(include=['twiget']),

    py_modules=['twiget_cli'],

    python_requires='>=3.6, <4',

    install_requires=['requests'],

    entry_points={
        'console_scripts': [
            'twiget-cli=twiget_cli:main',
        ],
    },

    project_urls={
        'Bug Reports': 'https://github.com/aesuli/twiget/issues',
        'Source': 'https://github.com/aesuli/twiget/',
    },
)