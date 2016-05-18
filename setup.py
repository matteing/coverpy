from setuptools import setup, find_packages

setup(
	name='coverpy',
	version='0.8',
	packages=find_packages(exclude=['scripts', 'tests']),
	install_requires=['requests'],
	license='MIT License',
	author="fallenshell",
	author_email='dev@mxio.us',
	description="A wrapper for iTunes Search API",
	long_description=open('README.md').read(),
	package_data = {
		'': ['*.txt', '*.md'],
	}
)
