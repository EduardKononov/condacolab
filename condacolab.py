"""
condacolab.py
Install Conda and friends on Google Colab, easily
"""

import shutil
from urllib.request import urlopen
from subprocess import call
import os
import sys
from pathlib import Path
import time
from distutils.spawn import find_executable

PREFIX = "/usr/local"


def install_from_url(installer_url, prefix=PREFIX, inject=True):
    """
    Install Miniconda
    """

    print(f"⬇ Downloading {installer_url}...")
    installer_fn = "_miniconda_installer_.sh"
    with urlopen(installer_url) as response, open(installer_fn, "wb") as out:
        shutil.copyfileobj(response, out)
    print("📦 Installing...")
    call(["bash", installer_fn, "-bfp", prefix])
    os.unlink(installer_fn)

    print("📌 Configuring pinnings...")
    cuda_version = ".".join(os.environ.get("CUDA_VERSION", "*.*.*").split(".")[:2])
    prefix = Path(prefix)
    condameta = prefix / "conda-meta"
    condameta.mkdir(parents=True, exist_ok=True)
    pymaj, pymin = sys.version_info[:2]

    with open(condameta / "pinned", "a") as f:
        f.write(f"python {pymaj}.{pymin}.*\n")
        f.write(f"python_abi {pymaj}.{pymin}.* *cp{pymaj}{pymin}*\n")
        f.write(f"cudatoolkit {cuda_version}.*\n")

    with open(prefix / ".condarc", "a") as f:
        f.write("always_yes: true\n")

    if inject:
        print("🔁 Kernel will now restart!")
        print("ℹ If the cell keeps spinning, just ignore it.")
        print("  Wait five seconds and run the following cells as usual.")
        time.sleep(3)
        patch_env_vars(prefix)
    else:
        sitepackages = f"{prefix}/lib/python{pymaj}.{pymin}/site-packages"
        if sitepackages not in sys.path:
            sys.path.insert(0, sitepackages)


def install(prefix=PREFIX, inject=True):
    installer_url = r"https://github.com/jaimergp/miniforge/releases/download/refs%2Fpull%2F1%2Fmerge/Mambaforge-colab-Linux-x86_64.sh"
    return install_from_url(installer_url, prefix=prefix, inject=inject)


install_mambaforge = install


def install_miniconda(prefix=PREFIX, inject=True):
    installer_url = r"https://repo.continuum.io/miniconda/Miniconda3-4.5.4-Linux-x86_64.sh"
    return install_from_url(installer_url, prefix=prefix, inject=inject)


def patch_env_vars(prefix):
    """
    TODO: `os.execve` works but is unreliable. Sometimes the kernel does not reconnect!

    Other things to (re)try:

    * Adding env vars to /etc/share/jupyter/.../kernel.json & do a clean kernel restart
    """

    pymaj, pymin = sys.version_info[:2]
    sitepackages = f"{prefix}/lib/python{pymaj}.{pymin}/site-packages"
    os.environ["PYTHONPATH"] = f"{sitepackages}:{os.environ.get('PYTHONPATH', '')}"
    os.environ["LD_LIBRARY_PATH"] = f"{prefix}/lib:{os.environ.get('LD_LIBRARY_PATH', '')}"
    os.execve(sys.executable, [sys.executable] + sys.argv, os.environ)


def check(prefix=PREFIX):
    assert find_executable("conda"), "💥💔💥 Conda not found!"
    assert find_executable("mamba"), "💥💔💥 Mamba not found!"

    pymaj, pymin = sys.version_info[:2]
    sitepackages = f"{prefix}/lib/python{pymaj}.{pymin}/site-packages"
    assert (
        sitepackages in os.environ["PYTHONPATH"]
    ), f"💥💔💥 PYTHONPATH was not patched! Value: {os.environ['PYTHONPATH']}"
    assert (
        f"{prefix}/lib" in os.environ["LD_LIBRARY_PATH"]
    ), f"💥💔💥 LD_LIBRARY_PATH was not patched! Value: {os.environ['LD_LIBRARY_PATH']}"
    print("✨🍰✨ Everything looks OK!")