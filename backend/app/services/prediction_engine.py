"""Deterministic prior authorization approval likelihood scoring."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from app.services.nlp_extractor import ExtractionResult


@dataclass
class PolicyGap:
    code: str
    description: str
    severity: str  # required | recommended


@dataclass
class PredictionResult:
    approval_likelihood_score: float  # 0-100
    policy_id: str | None
    policy_name: str | None
    matched_criteria: list[str] = field(default_factory=list)
    documentation_gaps: list[PolicyGap] = field(default_factory=list)
    scoring_breakdown: dict[str, float] = field(default_factory=dict)
    recommendation: str = ""


class PredictiveRulesEngine:
    """Evaluate extracted FHIR criteria against mock payer policies."""

    def __init__(self, rulebook_path: Path | None = None):
        path = rulebook_path or Path(__file__).resolve().parents[2] / "data" / "payer_policy_rulebook.json"
        self._rulebook = json.loads(path.read_text(encoding="utf-8"))

    def predict(self, extraction: ExtractionResult, note_text: str = "") -> PredictionResult:
        policy = self._match_policy(extraction)
        if policy is None:
            return PredictionResult(
                approval_likelihood_score=0.0,
                policy_id=None,
                policy_name=None,
                recommendation="No matching payer policy found for extracted criteria.",
                documentation_gaps=[
                    PolicyGap("NO_POLICY_MATCH", "No payer policy matches extracted codes", "required")
                ],
            )

        return self._score_policy(policy, extraction, note_text)

    def predict_from_cer(self, cer: dict, note_text: str = "") -> PredictionResult:
        from app.services.nlp_extractor import ClinicalNLPExtractor, ExtractedEntity

        entities = []
        for item in cer.get("item", []):
            coding = (item.get("productOrService") or {}).get("coding", [{}])[0]
            if coding.get("system", "").endswith("cpt"):
                entities.append(
                    ExtractedEntity("procedure", coding.get("display", ""), coding.get("code"),
                                    coding.get("system"), 0.9)
                )
            elif "rxnorm" in coding.get("system", ""):
                entities.append(
                    ExtractedEntity("medication", coding.get("display", ""), coding.get("code"),
                                    coding.get("system"), 0.9)
                )
            for dx in item.get("diagnosis", []):
                dc = dx.get("diagnosisCodeableConcept", {}).get("coding", [{}])[0]
                entities.append(
                    ExtractedEntity("condition", dc.get("display", ""), dc.get("code"), dc.get("system"), 0.9)
                )

        extraction = ExtractionResult(entities=entities, coverage_eligibility_request=cer)
        return self.predict(extraction, note_text)

    def _match_policy(self, extraction: ExtractionResult) -> dict | None:
        proc_codes = {e.code for e in extraction.entities if e.entity_type == "procedure" and e.code}
        med_codes = {e.code for e in extraction.entities if e.entity_type == "medication" and e.code}
        dx_codes = {e.code for e in extraction.entities if e.entity_type == "condition" and e.code}

        best: dict | None = None
        best_score = -1

        for policy in self._rulebook["policies"]:
            match = policy["match"]
            score = 0
            dimensions = 0
            satisfied = 0

            if match.get("procedure_codes"):
                dimensions += 1
                overlap = proc_codes.intersection(match["procedure_codes"])
                if overlap:
                    satisfied += 1
                    score += len(overlap) * 2
            if match.get("medication_codes"):
                dimensions += 1
                overlap = med_codes.intersection(match["medication_codes"])
                if overlap:
                    satisfied += 1
                    score += len(overlap) * 2
            if match.get("diagnosis_codes"):
                dimensions += 1
                overlap = dx_codes.intersection(match["diagnosis_codes"])
                if overlap:
                    satisfied += 1
                    score += len(overlap)

            if dimensions == 0:
                continue
            # Match if at least one required dimension hits; prefer highest score
            if satisfied > 0 and score > best_score:
                best = policy
                best_score = score

        return best

    def _score_policy(self, policy: dict, extraction: ExtractionResult, note_text: str) -> PredictionResult:
        weights = policy.get("weights", {})
        requirements = policy.get("requirements", {})
        entity_types = {e.entity_type for e in extraction.entities}
        matched: list[str] = []
        gaps: list[PolicyGap] = []
        breakdown: dict[str, float] = {}
        score = 0.0

        # Conservative therapy check
        min_weeks = requirements.get("min_conservative_therapy_weeks")
        if min_weeks is not None:
            weeks = extraction.conservative_therapy_weeks
            if weeks is not None and weeks >= min_weeks:
                pts = weights.get("conservative_therapy_met", 30)
                score += pts
                breakdown["conservative_therapy_met"] = pts
                matched.append(f"Conservative therapy {weeks} weeks (≥{min_weeks} required)")
            else:
                gaps.append(
                    PolicyGap(
                        "CONSERVATIVE_THERAPY_INSUFFICIENT",
                        f"Document ≥{min_weeks} weeks failed conservative therapy (found: {weeks})",
                        "required",
                    )
                )

        # Imaging mention
        if "MRI" in note_text.upper() or "CT" in note_text.upper():
            pts = weights.get("has_imaging", 25)
            score += pts
            breakdown["has_imaging"] = pts
            matched.append("Imaging study referenced in clinical note")
        elif "imaging" in str(requirements.get("required_documentation", [])).lower():
            gaps.append(PolicyGap("MISSING_IMAGING", "MRI or CT imaging report required", "required"))

        # Entity type requirements
        for req_entity in requirements.get("required_entities", []):
            if req_entity in entity_types:
                key = f"{req_entity}_match"
                pts = weights.get(key, weights.get("diagnosis_match", 10))
                if key in weights or req_entity in ("condition", "procedure", "medication"):
                    breakdown[key] = breakdown.get(key, 0) + pts
                    score += pts if key in weights else 0
                matched.append(f"Required entity present: {req_entity}")
            else:
                gaps.append(
                    PolicyGap(f"MISSING_{req_entity.upper()}", f"Required entity not extracted: {req_entity}", "required")
                )

        # Documentation checklist gaps
        doc_items = requirements.get("required_documentation", [])
        note_lower = note_text.lower()
        for doc in doc_items:
            keywords = doc.lower().split()[:3]
            if not any(kw in note_lower for kw in keywords if len(kw) > 3):
                gaps.append(PolicyGap("DOC_GAP", doc, "recommended"))

        score = min(score, 100.0)
        if score >= 80:
            recommendation = "Likely approved — criteria substantially met"
        elif score >= 50:
            recommendation = "Conditional — additional documentation recommended before submission"
        else:
            recommendation = "Unlikely to approve — significant criteria gaps"

        return PredictionResult(
            approval_likelihood_score=round(score, 1),
            policy_id=policy["id"],
            policy_name=policy["name"],
            matched_criteria=matched,
            documentation_gaps=gaps,
            scoring_breakdown=breakdown,
            recommendation=recommendation,
        )
