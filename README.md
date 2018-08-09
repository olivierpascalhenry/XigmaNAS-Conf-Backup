Version
-------
XigmaNAS Conf Backup 1.0.1


Project Overview:
-----------------
XigmaNAS Conf Backup is a small tool to download and backup the configuration .xml file from a XigmaNAS-based NAS.


Compatibility:
--------------
    - sources : linux, windows, macos
    - binaries : linux, windows


Install instructions for binaries:
---------------------------------------
Download and install the last binary file in the Release directory. Actually, the binary file is only compatible with Windows (from Windows 7 32) and Linux (from Ubuntu 14.04). The software should be installed in the Home directory for Linux, and outside the Program Files directory for Windows to avoid issues with Windows admin protections.


Install instructions for sources:
--------------------------------------
Download sources and uncompress them somewhere on your hard drive. Open a terminal in the new directory and launch XigmaNAS Conf Backup by typing: python xigmanas_conf_backup.py. Do not forget to install dependencies.


External libraries:
-------------------
* PyQt5 v5.10+
* paramiko v2.4.1+
* requests v2.18+
