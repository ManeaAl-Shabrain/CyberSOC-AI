import pytest

from cybersoc.correlation import correlate, severity_for
from cybersoc.scenarios import context_records, dataset, evidence_for, generate_events, synthetic_case


@pytest.mark.parametrize("scenario", dataset().scenarios, ids=lambda scenario: scenario.id)
def test_replay_and_baseline(scenario):
    first = generate_events(scenario)
    second = generate_events(scenario)
    assert first == second
    assert [evidence_for(item) for item in first] == [evidence_for(item) for item in second]
    cluster = correlate(first)
    assert cluster == correlate(list(reversed(first)))
    assert severity_for(cluster, scenario.privileged, scenario.change) == scenario.expected
    assert len({item.event_id for item in [*first, *context_records(scenario)]}) == len(first) + 2


def test_optional_lookup_returns_none():
    assert synthetic_case("absent") is None
