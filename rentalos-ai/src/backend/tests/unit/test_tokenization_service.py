from src.backend.services.tokenization_service import list_tokens, tokenize_asset


def test_tokenize_asset_records_holder():
    record = tokenize_asset(5, "Investor", 12.5)
    assert record.asset_id == 5
    assert list_tokens()
