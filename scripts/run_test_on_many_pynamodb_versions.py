# -*- coding: utf-8 -*-

"""
Manually run unit test on different combination of pynamodb versions.
"""

import subprocess
from pynamodb_mate.paths import dir_project_root, dir_venv_bin

pynamodb_versions = [
    "5.5.1",
]
path_venv_pip = dir_venv_bin / "pip"
with dir_project_root.cwd():
    for version in pynamodb_versions:
        subprocess.run(
            [
                f"{path_venv_pip}",
                "install",
                f"pynamodb=={version}",
            ]
        )
        subprocess.run(["pyops", "cov-only"])
