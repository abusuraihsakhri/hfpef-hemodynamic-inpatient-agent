"""
Automated Pytest Test Suite for Hfpef Hemodynamic Inpatient Agent.
Domain: Cardiology & Intensive Care Systems
Standard: AHA/ACC Guidelines / Surviving Sepsis Campaign
"""
import os
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from agents.base import PHIGuard, AuditLogger, SecurityException, AuditTrail
from agents.models import SystemTaskPayload, UrgencyLevel, SystemIntegrityStatus
from agents.workers import InvariantQCWorker, SafetyEscalationWorker, ProtocolConformanceWorker
from agents.supervisor import SystemSupervisor
from cli import main


def test_phi_guard_enforcement():
    with pytest.raises(SecurityException):
        PHIGuard.assert_no_phi("Patient MRN-994827 blood culture positive for Staphylococcus")

    # Clean text passes
    PHIGuard.assert_no_phi("Analytical assay specimen KEY-001 optimal")


def test_phi_redaction():
    """Test that PHI patterns are properly redacted."""
    text_with_phi = "Patient John Doe has MRN-123456 and SSN 123-45-6789"
    redacted = PHIGuard.redact_phi(text_with_phi)
    assert "John Doe" not in redacted
    assert "MRN-123456" not in redacted
    assert "123-45-6789" not in redacted
    assert "[REDACTED_IDENTIFIER]" in redacted


def test_phi_guard_email_detection():
    """Test that email addresses are detected as PHI."""
    with pytest.raises(SecurityException):
        PHIGuard.assert_no_phi("Contact patient at john.doe@hospital.com")


def test_phi_guard_phone_detection():
    """Test that phone numbers are detected as PHI."""
    with pytest.raises(SecurityException):
        PHIGuard.assert_no_phi("Call patient at 555-123-4567")


def test_specialized_workers():
    # Worker 1: QC Invariant
    p1 = SystemTaskPayload(task_id="T1", target_identifier="KEY-01", primary_metric=35.0)
    alerts1 = InvariantQCWorker.evaluate(p1)
    assert len(alerts1) == 1
    assert alerts1[0].urgency == UrgencyLevel.ELEVATED

    # Worker 2: Safety
    p2 = SystemTaskPayload(task_id="T2", target_identifier="KEY-02", primary_metric=10.0, is_critical_flag=True)
    alerts2 = SafetyEscalationWorker.evaluate(p2)
    assert len(alerts2) == 1
    assert alerts2[0].urgency == UrgencyLevel.CRITICAL_STAT

    # Worker 3: Protocol Conformance
    p3 = SystemTaskPayload(task_id="T3", target_identifier="KEY-03", primary_metric=10.0, status_descriptor="DISCORDANT_ANOMALY")
    alerts3 = ProtocolConformanceWorker.evaluate(p3)
    assert len(alerts3) == 1


def test_supervisor_consensus_and_audit():
    supervisor = SystemSupervisor(model_provider="mock")
    payload = SystemTaskPayload(
        task_id="TASK-PROD-01",
        target_identifier="KEY-PROD-01",
        primary_metric=12.0,
        secondary_metric=4.0,
        status_descriptor="NOMINAL"
    )
    dossier = supervisor.process_task(payload)
    assert dossier.overall_urgency == UrgencyLevel.ROUTINE
    assert dossier.integrity_status == SystemIntegrityStatus.VALIDATED
    assert dossier.audit_hash != ""

    # Verify cryptographic audit trail
    assert AuditLogger.verify_integrity() is True

    # CLI tests
    assert main(["audit", "--task-id", "CLI-TEST-01"]) == 0
    assert main(["chat", "Explain", "specifications"]) == 0
    assert main(["verify-audit"]) == 0


def test_audit_trail_integrity():
    """Test that audit trail detects tampering."""
    trail = AuditTrail(secret_key="test-key")
    trail.log("test", "tier1", "EVENT_1", {"data": "value1"})
    trail.log("test", "tier1", "EVENT_2", {"data": "value2"})
    assert trail.verify_integrity() is True

    # Tamper with the hash chain by modifying a current_hash
    trail.logs[0]["current_hash"] = "tampered_hash_value_000000000000"
    assert trail.verify_integrity() is False


def test_batch_missing_file():
    """Test that batch command handles missing input file gracefully."""
    result = main(["batch", "-i", "/nonexistent/path/file.csv"])
    assert result == 1


def test_batch_with_sample_csv():
    """Test batch processing with the sample CSV file."""
    result = main(["batch", "-i", "sample.csv", "-o", "test_output.csv"])
    assert result == 0
    # Verify output file was created
    assert os.path.exists("test_output.csv")
    # Clean up
    os.remove("test_output.csv")


def test_audit_trail_with_secret():
    """Test that audit trail uses provided secret key."""
    trail = AuditTrail(secret_key="my-secret-key")
    entry = trail.log("actor", "tier", "EVENT", {"key": "value"})
    assert entry["current_hash"] != ""
    assert entry["prev_hash"] == "GENESIS_BLOCK_0000000000000000"


def test_empty_phi_guard():
    """Test that empty text passes PHI guard."""
    PHIGuard.assert_no_phi("")
    PHIGuard.assert_no_phi(" ")
