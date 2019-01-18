from setuptools import setup, find_packages

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

setup(
    name='futuremaker',
    version='1.0.0',
    author='gncloud',
    author_email='op@gncloud.kr',
    keywords=['gncloud', 'futuremaker', 'bitcoin'],
    description='futuremaker',
    packages=["futuremaker"],
    include_package_data=True,
    install_requires=install_requires,
    setup_requires=setup_requires,
    dependency_links=dependency_links,
    python_requires='>=3',
)