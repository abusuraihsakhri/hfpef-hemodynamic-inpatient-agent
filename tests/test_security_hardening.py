"""Regression checks for audit authenticity and synthetic-data boundaries."""

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from agents.api import app
from agents.base import AuditTrail, PHIGuard, SecurityException
from agents.llm_factory import LLMFactory
from agents.models import SystemTaskPayload
from agents.supervisor import SystemSupervisor


def test_audit_signature_detects_last_entry_tampering():
    trail = AuditTrail(secret_key="test-key")
    trail.log("system", "worker", "CHECK", {"value": 1})
    assert trail.verify_integrity()
    trail.logs[-1]["event_type"] = "FORGED"
    assert not trail.verify_integrity()


def test_audit_signature_detects_final_hash_replacement():
    trail = AuditTrail(secret_key="test-key")
    trail.log("system", "worker", "CHECK", {"value": 1})
    trail.logs[-1]["current_hash"] = "0" * 64
    assert not trail.verify_integrity()


def test_audit_log_reads_do_not_mutate_stored_entries():
    trail = AuditTrail(secret_key="test-key")
    trail.log("system", "worker", "CHECK", {"value": 1})
    snapshot = trail.get_trail()
    snapshot[0]["event_type"] = "MODIFIED"
    assert trail.verify_integrity()
    assert trail.get_trail()[0]["event_type"] == "CHECK"


def test_production_requires_audit_signing_key(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("AUDIT_SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError, match="AUDIT_SECRET_KEY"):
        AuditTrail()


def test_nested_sensitive_input_is_blocked_before_audit():
    payload = SystemTaskPayload(
        task_id="SYN-1",
        target_identifier="SYN-2",
        primary_metric=12,
        attributes={"observations": [{"patient_name": "Jane Person"}]},
    )
    with pytest.raises(SecurityException):
        SystemSupervisor().process_task(payload)


def test_guard_blocks_identifiers_in_nested_free_text():
    with pytest.raises(SecurityException):
        PHIGuard.assert_no_phi_payload({"meta": ["MRN-123456"]})


def test_api_rejects_phi_without_leaking_input():
    client = TestClient(app)
    response = client.post("/api/audit", json={
        "task_id": "SYN-1",
        "target_identifier": "SYN-2",
        "primary_metric": 5,
        "attributes": {"email": "person@example.org"},
    })
    assert response.status_code == 422
    assert "person@example.org" not in response.text


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_nonfinite_metrics_rejected(value):
    with pytest.raises(ValidationError):
        SystemTaskPayload(task_id="SYN-1", target_identifier="SYN-2", primary_metric=value)


def test_unimplemented_model_provider_is_not_silently_mocked():
    with pytest.raises(ValueError, match="not implemented"):
        LLMFactory.create("openai")
