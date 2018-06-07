import os
from setuptools import setup, find_packages

from irc2osc import __version__

readme = os.path.join(os.path.dirname(__file__), 'README.md')

setup(
    python_requires='>=3.5.2',
    name='irc2osc',
    version=__version__,
    url='https://github.com/MattBroach/irc2osc',
    author='Matt Nishi-Broach',
    author_email='go.for.dover@gmail.com',
    description='Bridge that takes incoming IRC messages and converts them to OSC messages',
    long_description=open(readme).read(),
    long_description_content_type='text/markdown',
    license='MIT',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'irc>=16.3',
        'python-osc>=1.6.6',
    ],
    extra_requires={
        'testing': [
            'flake8>=3.5.0',
        ]
    },
    entry_points={'console_scripts': [
        'irc2osc = irc2osc.cli:CLI.entrypoint'
    ]},
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Communications :: Chat :: Internet Relay Chat',
        'Topic :: Multimedia',
    ],
)
