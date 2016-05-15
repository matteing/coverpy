                             
 ___ ___ _ _ ___ ___ ___ _ _ 
|  _| . | | | -_|  _| . | | |
|___|___|\_/|___|_| |  _|_  |
                    |_| |___| v1.0
                    
                    
Small wrapper for the iTunes API; mostly for fetching album covers. **Will soon be transferred over to Mxious, as it was built for it.** 

**Docs need to be done, I know. Been busy.**

## Install
The install process is currently screwed, as I am new to Python and don't understand packaging very well. It seems complicated. Will fix. Meanwhile, import the file manually.

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
