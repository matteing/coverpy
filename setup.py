from setuptools import setup, find_packages

setup(
	# PyPI specific meta
	name='coverpy',
	version='0.0.1',
	license='MIT License',
	author="fallenshell",
	author_email='dev@mxio.us',
	description="A wrapper for iTunes Search API",
	long_description=open('README.md').read(),
	keywords='itunes search api wrapper simple clear cover album art music',
	# Package routines
	packages=find_packages(exclude=['scripts', 'tests']),
	install_requires=['requests'],
)
