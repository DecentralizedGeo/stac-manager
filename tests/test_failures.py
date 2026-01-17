from stac_manager.failures import FailureCollector, FailureRecord

def test_add_failure():
    fc = FailureCollector()
    fc.add(item_id="item1", error="Bad thing", step_id="test_step")
    assert fc.count() == 1
    assert fc.count_by_step()["test_step"] == 1
    
    records = fc.get_all()
    assert len(records) == 1
    assert records[0].item_id == "item1"
    assert records[0].message == "Bad thing"
