"""
LIBER - Backend Entry Point
"""
from app import create_app
from app.utils.debug_log import dbg

# region agent log
dbg("E", "backend/run.py:8", "run_py_imported_create_app", {}, runId="post-fix")
# endregion
app = create_app()
