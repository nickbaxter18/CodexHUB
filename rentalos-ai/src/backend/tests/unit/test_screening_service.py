import pytest

from src.backend.services.screening_service import evaluate_applicant


@pytest.mark.asyncio
async def test_evaluate_applicant_scores_data():
    result = await evaluate_applicant({"name": "Alex", "credit_score": 720, "income": 60000})
    assert result.score >= 70
    assert result.fairness_flag is True
