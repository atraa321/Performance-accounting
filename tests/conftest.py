import os
import pytest

@pytest.fixture(scope="session")
def sample_excel_path():
    return os.path.join(os.path.dirname(__file__), "..", "samples", "绩效核算_最小测试样本.xlsx")

@pytest.fixture(scope="session")
def gold_excel_path():
    return os.path.join(os.path.dirname(__file__), "..", "samples", "绩效核算_最小测试样本金标准结果.xlsx")

@pytest.fixture(scope="session")
def api_base_url():
    # 若采用方式B（接口测试），可通过环境变量覆盖
    # 例如：export PERF_API_BASE_URL="http://127.0.0.1:8000"
    return os.getenv("PERF_API_BASE_URL", "http://127.0.0.1:8000")

@pytest.fixture(scope="session")
def run_month():
    return os.getenv("PERF_RUN_MONTH", "2025-12")
