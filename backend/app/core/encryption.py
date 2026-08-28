"""Backward-compatible PHI encryption facade delegating to envelope encryption."""

from app.core.envelope_encryption import EnvelopeEncryptionService, envelope_encryption

PHIEncryptionService = EnvelopeEncryptionService
phi_encryption = envelope_encryption
