import importlib
import json
import requests
import pytest

from .utils import read_gold_standard, normalize_rows, index_by_name, assert_close

def try_run_local_function(run_month: str, sample_excel_path: str):
    """方式A：尝试导入并调用纯函数。"""
    # 约定：app.calc.run_calculation(run_month, excel_path) -> dict
    try:
        mod = importlib.import_module("app.calc")
    except Exception:
        return None

    fn = getattr(mod, "run_calculation", None)
    if fn is None:
        return None

    result = fn(run_month=run_month, excel_path=sample_excel_path)
    if not isinstance(result, dict) or "rows" not in result:
        raise AssertionError("app.calc.run_calculation must return dict with key 'rows'")
    return result["rows"]

def run_via_api(api_base_url: str, run_month: str, sample_excel_path: str):
    """方式B：通过FastAPI接口跑一遍。"""
    # 1) create run
    r = requests.post(f"{api_base_url}/runs", json={"month": run_month, "dept_name":"TEST", "rule_version":"default"})
    r.raise_for_status()
    run_id = r.json().get("run_id") or r.json().get("id")
    assert run_id, f"Create run response missing run_id: {r.text}"

    # 2) import excel
    with open(sample_excel_path, "rb") as f:
        files = {"file": ("sample.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        r = requests.post(f"{api_base_url}/runs/{run_id}/import/excel", files=files)
    r.raise_for_status()

    # 3) calculate
    r = requests.post(f"{api_base_url}/runs/{run_id}/calculate")
    r.raise_for_status()

    # 4) fetch summary
    r = requests.get(f"{api_base_url}/runs/{run_id}/summary")
    r.raise_for_status()
    data = r.json()

    # Accept either {rows:[...]} or direct list
    rows = data["rows"] if isinstance(data, dict) and "rows" in data else data
    assert isinstance(rows, list), f"Summary must be list or dict with rows. Got: {type(data)}"
    return rows

@pytest.mark.integration
def test_gold_standard(sample_excel_path, gold_excel_path, api_base_url, run_month):
    gold = read_gold_standard(gold_excel_path)

    # Prefer local function if available
    rows = try_run_local_function(run_month, sample_excel_path)
    if rows is None:
        # fallback to API
        try:
            rows = run_via_api(api_base_url, run_month, sample_excel_path)
        except Exception as e:
            pytest.fail(
                "无法运行测试：未发现 app.calc.run_calculation，且 API 调用失败。\n"
                "请实现方式A（推荐）或启动服务并设置 PERF_API_BASE_URL。\n"
                f"Error: {e}"
            )

    rows = normalize_rows(rows)

    gold_idx = index_by_name(gold)
    got_idx = index_by_name(rows)

    # 1) 人员集合必须一致（至少包含金标准所有人）
    for name in gold_idx.keys():
        assert name in got_idx, f"Missing person in summary: {name}. Got names={list(got_idx.keys())}"

    # 2) 逐人逐项对齐到分
    for name, exp in gold_idx.items():
        got = got_idx[name]
        assert got["role"] == exp["role"], f"Role mismatch for {name}: got {got['role']} expected {exp['role']}"
        assert_close(got["direct_total"], exp["direct_total"])
        assert_close(got["pool_nursing"], exp["pool_nursing"])
        assert_close(got["pool_doctor"], exp["pool_doctor"])
        assert_close(got["surplus"], exp["surplus"])
        assert_close(got["grand_total"], exp["grand_total"])
