import pathlib
import setuptools


def from_file(*names, encoding='utf8'):
    with open(
        pathlib.Path(pathlib.Path(__file__).parent, *names),
        encoding=encoding
    ) as fil:
        return fil.read()


setuptools.setup(
    name='passtry',
    version='1.1.1',
    description='TODO',
    long_description=from_file('README.md'),
    url='https://github.com/rivsec/passtry',
    author='tasooshi',
    author_email='tasooshi@pm.me',
    project_urls={
        'Changelog': 'https://github.com/rivsec/passtry/CHANGELOG.md',
        'Issue Tracker': 'https://github.com/rivsec/passtry/issues',
    },
    keywords=[
    ],
    python_requires='>=3.10',
    install_requires=[
        'paramiko==2.11.0',
        'requests==2.28.0',
    ],
    packages=setuptools.find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    classifiers=[
    ],
    entry_points={
        'console_scripts': [
            'passtry = passtry:main'
        ]
    },
)
