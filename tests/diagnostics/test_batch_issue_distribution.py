from __future__ import annotations

from sosdiag import batch


def test_batch_aggregates_structured_parameter_warnings(monkeypatch):
    payloads = {
        "a": {
            "source": "a",
            "host": {"hostname": "host-a"},
            "diagnostics": [
                {
                    "id": "NET_KERNEL_PARAM",
                    "section": "4.2",
                    "title": "네트워크 커널 파라미터",
                    "status": "WARN",
                    "summary": "mismatch",
                    "include_in_report": True,
                    "current_values": {
                        "parameter_status": {
                            "net.core.netdev_max_backlog": "WARN",
                            "net.core.netdev_budget": "PASS",
                        }
                    },
                }
            ],
        },
        "b": {
            "source": "b",
            "host": {"hostname": "host-b"},
            "diagnostics": [
                {
                    "id": "NET_KERNEL_PARAM",
                    "section": "4.2",
                    "title": "네트워크 커널 파라미터",
                    "status": "WARN",
                    "summary": "mismatch",
                    "include_in_report": True,
                    "current_values": {
                        "parameter_status": {
                            "net.core.netdev_max_backlog": "WARN",
                            "vm.min_free_kbytes": "WARN",
                        }
                    },
                }
            ],
        },
    }
    monkeypatch.setattr(batch, "analyze_source", lambda source: payloads[str(source)])

    result = batch.analyze_corpus(["a", "b"])

    issues = result["issue_distribution"]["NET_KERNEL_PARAM"]
    assert issues["net.core.netdev_max_backlog"]["warn_count"] == 2
    assert issues["net.core.netdev_max_backlog"]["hosts"] == ["host-a", "host-b"]
    assert issues["vm.min_free_kbytes"]["warn_count"] == 1
    assert "net.core.netdev_budget" not in issues
