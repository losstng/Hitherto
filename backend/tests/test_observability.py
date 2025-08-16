from fastapi.testclient import TestClient

from backend.main import app
from backend.observability import track


@track("test_mod")
def _dummy():
    return 42


def test_metrics_endpoint_records_module_metrics():
    _dummy()
    client = TestClient(app)
    resp = client.get("/metrics")
    assert resp.status_code == 200
    body = resp.text
    assert 'module_success_total{module="test_mod"}' in body
    assert 'module_latency_seconds_count{module="test_mod"}' in body
