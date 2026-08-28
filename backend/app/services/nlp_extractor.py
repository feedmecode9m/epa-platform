"""Rule-based clinical NLP extraction for synthetic notes (no external APIs)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.schemas.fhir import CoverageEligibilityRequestResource


@dataclass
class ExtractedEntity:
    entity_type: str
    text: str
    code: str | None = None
    code_system: str | None = None
    confidence: float = 0.0


@dataclass
class ExtractionResult:
    entities: list[ExtractedEntity] = field(default_factory=list)
    conservative_therapy_weeks: int | None = None
    coverage_eligibility_request: dict | None = None
    confidence_score: float = 0.0


# Pattern library — lightweight rule-based NLP
ICD10_PATTERNS = [
    (re.compile(r"\bM51\.26\b", re.I), "M51.26", "Lumbar disc displacement"),
    (re.compile(r"\bM48\.062\b", re.I), "M48.062", "Spinal stenosis, lumbar"),
    (re.compile(r"\bM54\.5\b", re.I), "M54.5", "Low back pain"),
    (re.compile(r"\bE11\.?\d*\b", re.I), "E11.9", "Type 2 diabetes"),
    (re.compile(r"\bJ45\.?\d*\b", re.I), "J45.40", "Moderate persistent asthma"),
    (re.compile(r"disc herniation|herniated disc", re.I), "M51.26", "Lumbar disc herniation"),
    (re.compile(r"\bsteno(?:sis)?\b.*\blumbar\b|\blumbar\b.*\bsteno", re.I), "M48.062", "Lumbar stenosis"),
]

CPT_PATTERNS = [
    (re.compile(r"\b63030\b|microdiscectomy|laminotomy", re.I), "63030", "Laminotomy"),
    (re.compile(r"\blaminectomy\b", re.I), "63047", "Laminectomy"),
    (re.compile(r"\bMRI\b.*\b(lumbar|L4|L5|spine)\b", re.I), "72148", "MRI lumbar spine"),
]

MEDICATION_PATTERNS = [
    (re.compile(r"\bsemaglutide\b|\bOzempic\b", re.I), "1991302", "Semaglutide"),
    (re.compile(r"\bdupilumab\b", re.I), "1876376", "Dupilumab"),
    (re.compile(r"\bmetformin\b", re.I), "6809", "Metformin"),
]

CONSERVATIVE_THERAPY_PATTERN = re.compile(
    r"(\d+)\s*weeks?\s+(?:of\s+)?(?:(?:conservative\s+)?(?:physical\s+therapy|PT|conservative\s+treatment)|PT)",
    re.I,
)


class ClinicalNLPExtractor:
    """Extract structured PA criteria from unstructured clinical notes."""

    def extract(self, note_text: str, patient_reference: str, insurer_reference: str) -> ExtractionResult:
        entities: list[ExtractedEntity] = []
        note_lower = note_text.lower()

        for pattern, code, display in ICD10_PATTERNS:
            if pattern.search(note_text):
                entities.append(
                    ExtractedEntity(
                        entity_type="condition",
                        text=display,
                        code=code,
                        code_system="http://hl7.org/fhir/sid/icd-10-cm",
                        confidence=0.92,
                    )
                )

        for pattern, code, display in CPT_PATTERNS:
            if pattern.search(note_text):
                entities.append(
                    ExtractedEntity(
                        entity_type="procedure",
                        text=display,
                        code=code,
                        code_system="http://www.ama-assn.org/go/cpt",
                        confidence=0.88,
                    )
                )

        for pattern, code, display in MEDICATION_PATTERNS:
            if pattern.search(note_text):
                entities.append(
                    ExtractedEntity(
                        entity_type="medication",
                        text=display,
                        code=code,
                        code_system="http://www.nlm.nih.gov/research/umls/rxnorm",
                        confidence=0.85,
                    )
                )

        therapy_weeks = None
        therapy_match = CONSERVATIVE_THERAPY_PATTERN.search(note_text)
        if therapy_match:
            therapy_weeks = int(therapy_match.group(1))
            entities.append(
                ExtractedEntity(
                    entity_type="conservative_therapy",
                    text=f"{therapy_weeks} weeks conservative therapy",
                    confidence=0.90,
                )
            )

        if "failed" in note_lower or "without improvement" in note_lower:
            entities.append(
                ExtractedEntity(
                    entity_type="clinical_justification",
                    text="Conservative treatment failure documented",
                    confidence=0.87,
                )
            )

        cer = self._build_coverage_eligibility_request(
            entities, patient_reference, insurer_reference, therapy_weeks
        )
        avg_confidence = sum(e.confidence for e in entities) / len(entities) if entities else 0.0

        return ExtractionResult(
            entities=entities,
            conservative_therapy_weeks=therapy_weeks,
            coverage_eligibility_request=cer,
            confidence_score=round(avg_confidence, 3),
        )

    def _build_coverage_eligibility_request(
        self,
        entities: list[ExtractedEntity],
        patient_ref: str,
        insurer_ref: str,
        therapy_weeks: int | None,
    ) -> dict:
        items = []
        diagnoses = []

        for entity in entities:
            if entity.entity_type == "procedure" and entity.code:
                items.append(
                    {
                        "category": {"coding": [{"code": "medical"}]},
                        "productOrService": {
                            "coding": [{"system": entity.code_system, "code": entity.code, "display": entity.text}]
                        },
                    }
                )
            elif entity.entity_type == "condition" and entity.code:
                diagnoses.append(
                    {
                        "diagnosisCodeableConcept": {
                            "coding": [{"system": entity.code_system, "code": entity.code, "display": entity.text}]
                        }
                    }
                )
            elif entity.entity_type == "medication" and entity.code:
                items.append(
                    {
                        "category": {"coding": [{"code": "drug"}]},
                        "productOrService": {
                            "coding": [{"system": entity.code_system, "code": entity.code, "display": entity.text}]
                        },
                    }
                )

        if items and diagnoses:
            items[0]["diagnosis"] = diagnoses

        cer: dict = {
            "resourceType": "CoverageEligibilityRequest",
            "status": "active",
            "purpose": ["auth-requirements", "benefits"],
            "patient": {"reference": patient_ref},
            "insurer": {"reference": insurer_ref},
            "created": datetime.now(UTC).isoformat(),
            "item": items,
        }

        if therapy_weeks is not None:
            cer["supportingInfo"] = [
                {"information": {"reference": f"#conservative-therapy-{therapy_weeks}w"}},
            ]

        return cer
