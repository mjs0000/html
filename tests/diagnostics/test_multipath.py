from sosdiag.diagnostics.network_storage import evaluate_multipath
from sosdiag.model.network_storage import MultipathFacts, MultipathMap, MultipathPath


def _healthy_path(device: str) -> MultipathPath:
    return MultipathPath(
        device=device,
        dm_status="active",
        checker_status="ready",
        path_status="running",
    )


def test_multipath_healthy_paths_pass() -> None:
    facts = MultipathFacts(
        maps=[MultipathMap(map_name="mpatha", paths=[_healthy_path("sda"), _healthy_path("sdb")])],
        effective_config_available=True,
    )

    result = evaluate_multipath(facts)

    assert result.status == "PASS"
    assert result.tables[0].rows[0]["usable_paths"] == 2
    assert result.tables[0].rows[0]["failed_paths"] == 0
    assert result.tables[1].rows[0]["dm_status"] == "active"
    assert result.tables[1].rows[0]["checker_status"] == "ready"
    assert result.tables[1].rows[0]["path_status"] == "running"


def test_multipath_non_running_path_warns() -> None:
    facts = MultipathFacts(
        maps=[
            MultipathMap(
                map_name="mpatha",
                paths=[
                    _healthy_path("sda"),
                    MultipathPath(
                        device="sdb",
                        dm_status="active",
                        checker_status="ready",
                        path_status="down",
                    ),
                ],
            )
        ],
        effective_config_available=True,
    )

    result = evaluate_multipath(facts)

    assert result.status == "WARN"
    assert result.tables[0].rows[0]["failed_paths"] == 1


def test_multipath_missing_path_column_does_not_fabricate_pass() -> None:
    facts = MultipathFacts(
        maps=[
            MultipathMap(
                map_name="mpatha",
                paths=[
                    _healthy_path("sda"),
                    MultipathPath(device="sdb", dm_status="active", checker_status="ready"),
                ],
            )
        ],
        effective_config_available=True,
    )

    result = evaluate_multipath(facts)

    assert result.status == "PASS"
    assert result.tables[0].rows[0]["redundancy_status"] == "SKIPPED"
    assert result.tables[0].rows[0]["unknown_paths"] == 1
