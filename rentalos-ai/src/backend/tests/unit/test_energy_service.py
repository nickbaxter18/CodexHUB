from src.backend.services.energy_service import list_energy_trades, record_energy_trade


def test_record_energy_trade():
    trade = record_energy_trade(3, 20.0, "buy", 0.18)
    assert trade.carbon_impact >= 0
    assert list_energy_trades()
    assert trade.recommendations
