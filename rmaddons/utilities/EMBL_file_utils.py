import subprocess
import os
import sys


def groupsharepath(f1):
    if os.name == 'nt': # pragma: no cover
        p = subprocess.Popen('net use', stdout=subprocess.PIPE)
        n_use = p.communicate()[0].decode(encoding='ansi')
        drive = f1[:f1.find(':\\') + 1]

        if drive:
            shareline = n_use[n_use.find(drive):]
            shareline = shareline[:shareline.find('\n')]
            shareline1 = shareline[shareline.rfind('\\') + 1:]
            share = shareline1[:shareline1.find(' ')]
            file1 = f1[f1.find(drive) + 3:]

        else:
            share1 = f1[f1.find('\\\\') + 2:]
            share = share1[:share1.find('\\')]
            f2 = f1[f1.rfind(share):]
            file1 = f2[f2.find('\\') + 1:]

        file1 = file1.replace('\\', '/')
        file1 = '/g/' + share + '/' + file1

    if sys.platform == 'darwin': # pragma: no cover
        file1 = f1.replace('Volumes', 'g')

    if 'linux' in sys.platform:
        file1 = f1

    return (file1)
