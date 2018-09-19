import os
from setuptools import setup, find_packages

from chat_transformer import __version__

readme = os.path.join(os.path.dirname(__file__), 'README.md')

setup(
    python_requires='>=3.5.3',
    name='chat_transformer',
    version=__version__,
    url='https://github.com/MattBroach/chat_transformer',
    author='Matt Nishi-Broach',
    author_email='go.for.dover@gmail.com',
    description='Bridge that takes incoming IRC messages and converts them to other formats',
    long_description=open(readme).read(),
    long_description_content_type='text/markdown',
    license='MIT',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'irc>=16.4',
        'python-osc>=1.6.6',
        'aiohttp>=3.3.2',
        'PyJWT==1.6.4',
    ],
    extra_requires={
        'testing': [
            'flake8>=3.5.0',
        ]
    },
    entry_points={'console_scripts': [
        'chat-transformer = chat_transformer.cli:CLI.entrypoint'
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
