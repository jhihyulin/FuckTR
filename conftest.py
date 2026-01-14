"""pytest 配置與共用 fixture"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def pytest_configure(config):
    """註冊自訂 markers"""
    config.addinivalue_line(
        "markers", "smoke: smoke tests for quick validation"
    )
    config.addinivalue_line(
        "markers", "timeout(seconds): set timeout for test in seconds"
    )
    config.addinivalue_line(
        "markers", "tr_login: test TR login functionality"
    )
    config.addinivalue_line(
        "markers", "tr_login_invalid: test invalid TR login scenarios"
    )
