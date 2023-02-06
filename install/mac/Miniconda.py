import sys
import subprocess
import urllib.request

class Miniconda():
    def __init__(self) -> None:
        pass
    
    def install(self) -> int:
        tup = urllib.request.urlretrieve("https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh","install/mac/miniconda.sh")
        if tup[0] is None:
            return -1
        code = subprocess.run("./install/mac/miniconda.sh",capture_output=True)
        print(code)
        return 0