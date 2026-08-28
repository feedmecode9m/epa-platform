"""Phase 2 pipeline tests — NLP extraction and prediction engine."""

from app.services.nlp_extractor import ClinicalNLPExtractor
from app.services.prediction_engine import PredictiveRulesEngine


SPINE_NOTE = (
    "MRI confirms L4-L5 disc herniation with radiculopathy. "
    "Patient completed 8 weeks of conservative physical therapy without improvement. "
    "Requesting lumbar microdiscectomy (CPT 63030)."
)


def test_nlp_extracts_spine_entities():
    extractor = ClinicalNLPExtractor()
    result = extractor.extract(
        SPINE_NOTE,
        "Patient/synth-patient-0000",
        "Organization/payer-aetna-synth",
    )
    entity_types = {e.entity_type for e in result.entities}
    assert "procedure" in entity_types
    assert "conservative_therapy" in entity_types
    assert result.conservative_therapy_weeks == 8
    assert result.coverage_eligibility_request is not None
    assert result.coverage_eligibility_request["resourceType"] == "CoverageEligibilityRequest"


def test_prediction_engine_scores_spine_case():
    extractor = ClinicalNLPExtractor()
    engine = PredictiveRulesEngine()
    extraction = extractor.extract(SPINE_NOTE, "Patient/synth-patient-0000", "Organization/payer-aetna-synth")
    prediction = engine.predict(extraction, SPINE_NOTE)
    assert prediction.policy_id == "spine-surgery-lumbar"
    assert prediction.approval_likelihood_score >= 50.0
    assert any("Conservative therapy" in c for c in prediction.matched_criteria)


def test_prediction_identifies_gaps_for_insufficient_therapy():
    extractor = ClinicalNLPExtractor()
    engine = PredictiveRulesEngine()
    note = "MRI shows L4-L5 herniation. Patient had 2 weeks of PT. Request laminectomy."
    extraction = extractor.extract(note, "Patient/synth-patient-0000", "Organization/payer-aetna-synth")
    prediction = engine.predict(extraction, note)
    gap_codes = {g.code for g in prediction.documentation_gaps}
    assert "CONSERVATIVE_THERAPY_INSUFFICIENT" in gap_codes
