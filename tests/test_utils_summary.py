from stac_manager.utils import generate_processing_summary
from stac_manager.failures import FailureCollector
from unittest.mock import MagicMock

def test_summary_generation():
    result = {"name": "test", "total_steps": 2, "success": 1, "failed": 1}
    # Create a real FailureCollector to ensure compatibility
    # But FailureCollector might keep state, so usually we'd pass it in.
    fc = FailureCollector()
    # Manually adding a failure record if the internal structure allows, 
    # or using the add() method if it exists and we mock what it needs.
    # Looking at prior context, FailureCollector isn't fully visible, but we assume it has add().
    # Let's verify FailureCollector structure or just mock the whole thing.
    
    # Mocking FailureCollector to avoid dependency on its implementation details
    fc_mock = MagicMock(spec=FailureCollector)
    fc_mock.count.return_value = 1
    
    # Mocking the get_all returns
    fail_record = MagicMock()
    fail_record.step_id = "step1"
    fc_mock.get_all.return_value = [fail_record]
    
    summary = generate_processing_summary(result, fc_mock)
    
    assert "Workflow: test" in summary
    assert "step1: 1 failures" in summary
    assert "Total Failures: 1" in summary
