# -*- coding: utf-8 -*-

if __name__ == "__main__":
    from pynamodb_mate.tests.helper import run_cov_test

    run_cov_test(__file__, "pynamodb", is_folder=True, preview=False)
