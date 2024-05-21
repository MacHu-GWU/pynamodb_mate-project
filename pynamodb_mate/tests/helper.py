# -*- coding: utf-8 -*-

from ..paths import dir_project_root, dir_htmlcov
from ..vendor.pytest_cov_helper import run_cov_test as _run_cov_test


def run_cov_test(
    script: str, module: str, preview: bool = False, is_folder: bool = False
):
    _run_cov_test(
        script=script,
        module=module,
        root_dir=f"{dir_project_root}",
        htmlcov_dir=f"{dir_htmlcov}",
        preview=preview,
        is_folder=is_folder,
    )
