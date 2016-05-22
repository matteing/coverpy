# coverpy
[![Build Status](https://travis-ci.org/fallenshell/coverpy.svg?branch=master)](https://travis-ci.org/fallenshell/coverpy) [![Scrutinizer Code Quality](https://scrutinizer-ci.com/g/fallenshell/coverpy/badges/quality-score.png?b=master)](https://scrutinizer-ci.com/g/fallenshell/coverpy/?branch=master)

Small wrapper for the iTunes API; mostly for fetching album covers. 

## Install
This library requires Python 3.0+. It might work, but proceed with caution.

`pip install coverpy`

For development installs:

`make install`

## Testing
We have a Travis CI instance that unit tests automatically on commits. To run code coverage tests and unit tests, run:

`make test`

## Usage
Usage is very simple:
  
    # Instance CoverPy
    coverpy = coverpy.CoverPy()
    # Set a limit. There is a default (1), but I set it manually to showcase usage.
    limit = 1
    # Get results. Returns a Result object.
    result = coverpy.get_cover("OK Computer", limit)
    
    # Set a size for the artwork (first parameter) and get the result url.
    print result.artwork(100)
