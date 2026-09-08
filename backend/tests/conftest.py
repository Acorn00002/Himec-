import os
import tempfile
from pathlib import Path

_test_db_path = Path(tempfile.gettempdir()) / "ecca_test.db"
if _test_db_path.exists():
    _test_db_path.unlink()

os.environ["DATABASE_URL"] = f"sqlite:///{_test_db_path}"
