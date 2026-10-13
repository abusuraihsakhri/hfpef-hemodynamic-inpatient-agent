"""
Enterprise Security, PHI Outbound Guard, and HMAC-SHA256 Audit Trail.

"""
import os
import re
import json
import time
import hmac
import hashlib
import secrets
import threading
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

PHI_PATTERNS = [
    re.compile(r"\b(?:MRN|mrn)[:#\s-]*\d{4,10}\b", re.IGNORECASE),
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
    re.compile(r"\b(?:DOB|Date of Birth)[:\s]*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", re.IGNORECASE),
    re.compile(r"\b(?:Patient\s+Name|Patient)[:\s]+[A-Z][a-z]+\s+[A-Z][a-z]+\b", re.IGNORECASE),
    re.compile(r"\b(?:John\s+Doe|Jane\s+Smith|Alice\s+Johnson)\b", re.IGNORECASE),
]


class SecurityException(Exception):
    """Raised when outbound data violates HIPAA Safe Harbor or contains raw PHI."""
    pass


class ResourceLimitExceededException(Exception):
    """Raised when computational parameters exceed safety bounds."""
    pass


def assert_no_phi(text: str) -> None:
    if not text:
        return
    for pattern in PHI_PATTERNS:
        if pattern.search(str(text)):
            raise SecurityException(f"PHI Outbound Guard Violation: Sensitive identifier detected with pattern {pattern.pattern}")


def assert_no_phi_payload(value: Any) -> None:
    """Best-effort screening of strings and sensitive field names in nested data.

    This is a heuristic input guard, not HIPAA de-identification or a
    guarantee that arbitrary free text contains no patient information.
    """
    sensitive_fields = {
        "ssn", "socialsecuritynumber", "mrn", "medicalrecordnumber",
        "patientname", "patientfullname", "dateofbirth", "dob",
        "phone", "phonenumber", "email", "emailaddress",
    }
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = re.sub(r"[^a-z0-9]", "", str(key).lower())
            if normalized in sensitive_fields:
                raise SecurityException("Potential sensitive identifier field detected")
            assert_no_phi(str(key))
            assert_no_phi_payload(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            assert_no_phi_payload(item)
    elif isinstance(value, str):
        assert_no_phi(value)


class PHIGuard:
    @staticmethod
    def assert_no_phi(text: str) -> None:
        assert_no_phi(text)

    @staticmethod
    def assert_no_phi_payload(value: Any) -> None:
        assert_no_phi_payload(value)

    @staticmethod
    def redact_phi(text: str) -> str:
        res = str(text)
        for pattern in PHI_PATTERNS:
            res = pattern.sub("[REDACTED_IDENTIFIER]", res)
        return res


class AuditTrail:
    """Cryptographic Tamper-Evident HMAC-SHA256 Audit Trail."""
    def __init__(self, secret_key: Optional[str] = None):
        resolved_key = secret_key if secret_key is not None else os.getenv("AUDIT_SECRET_KEY")
        if not resolved_key:
            if os.getenv("APP_ENV", "").lower() == "production":
                raise RuntimeError("AUDIT_SECRET_KEY must be configured in production")
            import warnings
            warnings.warn(
                "AUDIT_SECRET_KEY not set; using an ephemeral development key. "
                "Audit signatures will not survive application restart.",
                RuntimeWarning,
                stacklevel=2,
            )
            resolved_key = secrets.token_hex(32)
        if os.getenv("APP_ENV", "").lower() == "production" and len(resolved_key.encode("utf-8")) < 32:
            raise RuntimeError("AUDIT_SECRET_KEY must contain at least 32 bytes in production")
        self.secret_key = resolved_key.encode("utf-8")
        self._lock = threading.RLock()
        self.logs: List[Dict[str, Any]] = []

    @staticmethod
    def _signed_fields(entry: Dict[str, Any]) -> str:
        """Unambiguous canonical encoding of the signed audit metadata."""
        keys = ("audit_id", "timestamp", "actor", "actor_tier",
                "event_type", "payload_hash", "prev_hash")
        return json.dumps({key: entry[key] for key in keys},
                          sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    def log(self, actor: str, actor_tier: str, event_type: str, details: Dict[str, Any]) -> Dict[str, Any]:
        assert_no_phi_payload(details)
        for field_value in (actor, actor_tier, event_type):
            assert_no_phi(field_value)
        payload_str = json.dumps(details, sort_keys=True, default=str)
        payload_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()
        with self._lock:
            entry = {
                "audit_id": f"AUDIT-{int(time.time() * 1000)}-{len(self.logs) + 1}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "actor": actor,
                "actor_tier": actor_tier,
                "event_type": event_type,
                "payload_hash": payload_hash,
                "prev_hash": self.logs[-1]["current_hash"] if self.logs
                    else "GENESIS_BLOCK_0000000000000000",
            }
            entry["current_hash"] = hmac.new(
                self.secret_key, self._signed_fields(entry).encode("utf-8"),
                hashlib.sha256
            ).hexdigest()
            self.logs.append(entry)
            return dict(entry)

    def verify_integrity(self) -> bool:
        """Recompute the signed hash for every block in a consistent snapshot."""
        with self._lock:
            entries = [dict(entry) for entry in self.logs]
        previous = "GENESIS_BLOCK_0000000000000000"
        for entry in entries:
            try:
                if not hmac.compare_digest(entry["prev_hash"], previous):
                    return False
                expected = hmac.new(
                    self.secret_key, self._signed_fields(entry).encode("utf-8"),
                    hashlib.sha256
                ).hexdigest()
                if not hmac.compare_digest(entry["current_hash"], expected):
                    return False
                previous = entry["current_hash"]
            except (KeyError, TypeError, ValueError):
                return False
        return True

    def get_trail(self) -> List[Dict[str, Any]]:
        """Return defensive copies without exposing the mutable live list."""
        with self._lock:
            return [dict(entry) for entry in self.logs]

GLOBAL_AUDIT = AuditTrail()


class AuditLogger:
    @staticmethod
    def log(actor: str, actor_tier: str, event_type: str, details: Dict[str, Any]) -> Dict[str, Any]:
        return GLOBAL_AUDIT.log(actor, actor_tier, event_type, details)

    @staticmethod
    def get_trail() -> List[Dict[str, Any]]:
        return GLOBAL_AUDIT.get_trail()

    @staticmethod
    def verify_integrity() -> bool:
        return GLOBAL_AUDIT.verify_integrity()
