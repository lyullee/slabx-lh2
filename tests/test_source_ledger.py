from slabx_lh2.source_ledger import SourceLedger, SourceState


def test_ledger_round_trip_and_validation(tmp_path):
    ledger = SourceLedger(
        substance="hydrogen", stage="pool", duration_s=120.0,
        states=(SourceState(10.0, 0.1, 1.0, 80.0, 0.08, 1.0),),
        observation_operator="LFL reach",
    )
    path = tmp_path / "source.json"
    ledger.write_json(path)
    assert SourceLedger.read_json(path).to_dict() == ledger.to_dict()


def test_pool_adapter_rejects_unresolved_liquid():
    ledger = SourceLedger(
        substance="hydrogen", stage="pool", duration_s=120.0,
        states=(SourceState(10.0, 0.1, 1.0, 80.0, 0.08, 1.0, liquid_fraction=0.2),),
    )
    try:
        ledger.to_evaporating_pool(substance=object())
    except ValueError as exc:
        assert "liquid" in str(exc)
    else:
        raise AssertionError("unresolved liquid state was accepted")
