"""
LIBER - Backend Entry Point
"""
from app import create_app
from app.utils.debug_log import dbg

# region agent log
dbg("E", "backend/run.py:8", "run_py_imported_create_app", {}, runId="post-fix")
# endregion
app = create_app()

if __name__ == '__main__':
    # region agent log
    dbg("E", "backend/run.py:13", "flask_run_starting", {"host": "0.0.0.0", "port": 5000}, runId="post-fix")
    # endregion
    app.run(debug=True, host='0.0.0.0', port=5000)

