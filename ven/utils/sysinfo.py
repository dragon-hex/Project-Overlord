"""
Sysinfo: all functions that get the system information.
"""

import sys

def getPythonVersion():
    """return the python version."""
    return str(sys.version_info.major) + "." + str(sys.version_info.minor) + "." + str(sys.version_info.micro)

def getSystem():
    """return the system name!"""
    import platform as _platform
    if _platform.system().lower() == 'linux':
        import distro as _distro
        return (
            0, 
            (_distro.linux_distribution()[0]+" "+_distro.linux_distribution()[1])
        )
    return (0, _platform.system())