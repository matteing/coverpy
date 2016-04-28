from setuptools import setup, find_packages

setup(
	name='coverpy',
	version='0.0.2dev',
	packages=find_packages(),
	install_requires=['requests'],
	license='MIT License',
	long_description=open('README.md').read(),
	package_data = {
		'': ['*.txt', '*.md'],
	},
)
