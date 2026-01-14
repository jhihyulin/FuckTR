"""pytest 配置與共用 fixture。"""

import sys
from pathlib import Path

# 確保根目錄在 Python path
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "smoke: smoke tests for quick validation"
    )
    config.addinivalue_line(
        "markers", "timeout(timeout): set timeout for test in seconds"
    )
