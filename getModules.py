import subprocess
import sys

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# List of packages to install
packages = ['plantcv', 'easygui', 'imageio', 'numpy', 'xlsxwriter', 'customtkinter', 'natsort', 'numba']

for package in packages:
    install(package)
