from __future__ import annotations

import glob
import runpy


def test_all_streamlit_pages_import_and_execute_without_crash() -> None:
    """Smoke test for page-level runtime exceptions.

    This executes each page module in bare mode (without `streamlit run`) to catch
    import/runtime regressions early in CI.
    """

    for path in sorted(glob.glob("app/pages/*.py")):
        runpy.run_path(path, run_name="__main__")
