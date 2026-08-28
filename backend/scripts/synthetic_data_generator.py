"""Generate HIPAA-safe synthetic FHIR R4 resources for local development."""

from __future__ import annotations

import argparse
import json
import random
import uuid
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

# Synthetic name pools — no real individuals
FIRST_NAMES = ["Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Quinn", "Avery"]
LAST_NAMES = ["Synth", "Testman", "Demo", "Mockley", "Fauxson", "Sampleton"]
PAYERS = [
    {"id": "payer-aetna-synth", "name": "Synthetic Aetna Health"},
    {"id": "payer-uhc-synth", "name": "Synthetic United Health"},
    {"id": "payer-bcbs-synth", "name": "Synthetic BCBS Regional"},
]

CLINICAL_NOTE_TEMPLATES = [
    (
        "MRI confirms L4-L5 disc herniation with radiculopathy. "
        "Patient completed 8 weeks of conservative physical therapy without improvement. "
        "Requesting lumbar microdiscectomy (CPT 63030)."
    ),
    (
        "Patient failed 6 weeks of conservative physical therapy for chronic lower back pain. "
        "Assessment: lumbar spondylosis with stenosis (M48.062). "
        "Recommend laminectomy evaluation."
    ),
    (
        "Type 2 diabetes poorly controlled on metformin. "
        "A1c 9.2%. Initiating GLP-1 agonist (semaglutide). "
        "Prior auth requested for Ozempic 0.5mg weekly."
    ),
    (
        "Moderate persistent asthma despite daily ICS/LABA. "
        "Adding biologic dupilumab after documented exacerbations x3 in 12 months."
    ),
]


def _uuid() -> str:
    return str(uuid.uuid4())


def generate_patient(index: int = 0) -> dict:
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    birth_year = random.randint(1955, 2005)
    return {
        "resourceType": "Patient",
        "id": f"synth-patient-{index:04d}",
        "meta": {"profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-patient"]},
        "identifier": [{"system": "urn:oid:synthetic-mrn", "value": f"MRN-SYN-{index:06d}"}],
        "name": [{"use": "official", "family": last, "given": [first]}],
        "gender": random.choice(["male", "female", "other"]),
        "birthDate": f"{birth_year}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
        "address": [
            {
                "use": "home",
                "line": [f"{100 + index} Synthetic Lane"],
                "city": "Devton",
                "state": "CA",
                "postalCode": "90000",
            }
        ],
    }


def generate_practitioner(index: int = 0) -> dict:
    return {
        "resourceType": "Practitioner",
        "id": f"synth-practitioner-{index:04d}",
        "identifier": [{"system": "http://npiregistry.example/synthetic", "value": f"NPI-SYN-{index:07d}"}],
        "name": [{"family": "Provider", "given": [f"Synthetic{index}"], "prefix": ["Dr."]}],
        "qualification": [{"code": {"text": "MD"}}],
    }


def generate_coverage(patient_id: str, index: int = 0) -> dict:
    payer = PAYERS[index % len(PAYERS)]
    return {
        "resourceType": "Coverage",
        "id": f"synth-coverage-{index:04d}",
        "status": "active",
        "beneficiary": {"reference": f"Patient/{patient_id}"},
        "payor": [{"reference": f"Organization/{payer['id']}"}],
        "class": [{"type": {"text": "plan"}, "value": f"SYN-PLAN-{index:04d}"}],
        "period": {"start": "2024-01-01", "end": "2026-12-31"},
    }


def generate_organization(payer: dict) -> dict:
    return {
        "resourceType": "Organization",
        "id": payer["id"],
        "name": payer["name"],
        "type": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/organization-type", "code": "ins"}]}],
    }


def generate_prior_auth_claim(patient_id: str, coverage_id: str, index: int = 0) -> dict:
    return {
        "resourceType": "Claim",
        "id": f"synth-claim-{index:04d}",
        "status": "active",
        "type": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/claim-type", "code": "professional"}]},
        "use": "preauthorization",
        "patient": {"reference": f"Patient/{patient_id}"},
        "insurer": {"reference": f"Organization/{PAYERS[index % len(PAYERS)]['id']}"},
        "created": datetime.now(UTC).isoformat(),
        "item": [
            {
                "sequence": 1,
                "productOrService": {
                    "coding": [{"system": "http://www.ama-assn.org/go/cpt", "code": "63030", "display": "Laminotomy"}]
                },
                "diagnosisSequence": [1],
            }
        ],
        "diagnosis": [
            {
                "sequence": 1,
                "diagnosisCodeableConcept": {
                    "coding": [
                        {
                            "system": "http://hl7.org/fhir/sid/icd-10-cm",
                            "code": "M51.26",
                            "display": "Other intervertebral disc displacement, lumbar region",
                        }
                    ]
                },
            }
        ],
        "insurance": [{"sequence": 1, "coverage": {"reference": f"Coverage/{coverage_id}"}}],
    }


def generate_clinical_note(index: int = 0) -> str:
    return CLINICAL_NOTE_TEMPLATES[index % len(CLINICAL_NOTE_TEMPLATES)]


def generate_bundle(count: int = 5) -> dict:
    entries = []
    for i in range(count):
        patient = generate_patient(i)
        practitioner = generate_practitioner(i)
        coverage = generate_coverage(patient["id"], i)
        payer_org = generate_organization(PAYERS[i % len(PAYERS)])
        claim = generate_prior_auth_claim(patient["id"], coverage["id"], i)
        note = generate_clinical_note(i)

        for resource in (patient, practitioner, coverage, payer_org, claim):
            entries.append({"fullUrl": f"urn:uuid:{resource['id']}", "resource": resource})

        entries.append(
            {
                "fullUrl": f"urn:uuid:note-{i:04d}",
                "resource": {
                    "resourceType": "DocumentReference",
                    "id": f"synth-note-{i:04d}",
                    "status": "current",
                    "type": {"text": "Progress Note"},
                    "subject": {"reference": f"Patient/{patient['id']}"},
                    "description": note,
                },
            }
        )

    return {
        "resourceType": "Bundle",
        "type": "collection",
        "timestamp": datetime.now(UTC).isoformat(),
        "entry": entries,
    }


def generate_dataset(count: int = 5, output_dir: Path | None = None) -> dict:
    bundle = generate_bundle(count)
    result = {
        "generated_at": datetime.now(UTC).isoformat(),
        "disclaimer": "SYNTHETIC DATA ONLY — NOT REAL PHI",
        "patient_count": count,
        "bundle": bundle,
        "clinical_notes": [generate_clinical_note(i) for i in range(count)],
    }
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        out_file = output_dir / "synthetic_fhir_bundle.json"
        out_file.write_text(json.dumps(result, indent=2), encoding="utf-8")
        notes_file = output_dir / "synthetic_clinical_notes.json"
        notes_file.write_text(json.dumps(result["clinical_notes"], indent=2), encoding="utf-8")
        print(f"Wrote {out_file}")
        print(f"Wrote {notes_file}")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic FHIR R4 test data")
    parser.add_argument("--count", type=int, default=5, help="Number of synthetic patients")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/synthetic"),
        help="Output directory for JSON files",
    )
    args = parser.parse_args()
    generate_dataset(args.count, args.output)


if __name__ == "__main__":
    main()
