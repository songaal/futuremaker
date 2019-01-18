import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setup_requires = []

install_requires = [
    'bitmex',
    'websockets',
    'aiohttp',
    'asyncio',
    'pandas',
    'pytz',
    'python-telegram-bot',
    ]

dependency_links = []

setuptools.setup(
    name="futuremaker",
    version="0.0.1",
    author="SongSangWook",
    author_email="swsong@gncloud.kr",
    description="Cryptocurrency trading library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/gncloud/futuremaker",
    packages=setuptools.find_packages(),
    install_requires=install_requires,
    setup_requires=setup_requires,
    dependency_links=dependency_links,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)