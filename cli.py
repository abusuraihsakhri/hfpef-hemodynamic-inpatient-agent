"""
Command Line Interface for Hfpef Hemodynamic Inpatient Agent.
"""
import argparse
import csv
import json
import os
import sys
from pathlib import Path
from agents.models import SystemTaskPayload
from agents.supervisor import SystemSupervisor
from agents.base import AuditLogger, SecurityException

supervisor = SystemSupervisor(model_provider="mock")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="hfpef-hemodynamic-inpatient-agent", description="Hfpef Hemodynamic Inpatient Agent")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Audit
    p_audit = subparsers.add_parser("audit", help="Run single task evaluation")
    p_audit.add_argument("--task-id", default="TASK-2026-001")
    p_audit.add_argument("--target", default="KEY-TARGET-01")
    p_audit.add_argument("--primary", type=float, default=28.5)
    p_audit.add_argument("--secondary", type=float, default=14.2)
    p_audit.add_argument("--critical", action="store_true")
    p_audit.add_argument("--status", default="DISCORDANT")

    # Chat
    p_chat = subparsers.add_parser("chat", help="System configuration query")
    p_chat.add_argument("query", nargs="+")

    # Batch
    p_batch = subparsers.add_parser("batch", help="Batch process CSV records")
    p_batch.add_argument("-i", "--input", required=True)
    p_batch.add_argument("-o", "--output", default="results.csv")

    # Verify Audit
    subparsers.add_parser("verify-audit", help="Verify HMAC audit trail integrity")

    # Serve
    p_serve = subparsers.add_parser("serve", help="Launch FastAPI REST server")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8000)

    args = parser.parse_args(argv)

    if args.command == "audit":
        payload = SystemTaskPayload(
            task_id=args.task_id,
            target_identifier=args.target,
            primary_metric=args.primary,
            secondary_metric=args.secondary,
            status_descriptor=args.status,
            is_critical_flag=args.critical,
        )
        dossier = supervisor.process_task(payload)
        print("=" * 80)
        print(f"  HFPEF HEMODYNAMIC INPATIENT AGENT")
        print(f"  Illustrative unitless thresholds only | Not validated for patient-care decisions")
        print(f"  Dossier ID: {dossier.dossier_id} | Urgency: [{dossier.overall_urgency.value}]")
        print("=" * 80)
        for a in dossier.alerts:
            print(f"\n  [{a.urgency.value}] from {a.origin_worker}:")
            print(f"  Summary: {a.summary}")
            print(f"  Details: {a.technical_details}")
            print(f"  Action:  {a.actionable_remediation}")
        print(f"\n  HMAC-SHA256 Audit Hash: {dossier.audit_hash}")
        print("=" * 80)
        return 0

    if args.command == "chat":
        ans = supervisor.query_supervisory_chat(" ".join(args.query))
        print(f"\n[Hfpef Hemodynamic Inpatient Agent Supervisor]:\n{ans}\n")
        return 0

    if args.command == "verify-audit":
        trail = AuditLogger.get_trail()
        valid = AuditLogger.verify_integrity()
        print(f"Audit Trail Blocks: {len(trail)} | Cryptographic Integrity Verified: {valid}")
        return 0

    if args.command == "batch":
        # Accept explicit absolute or relative input file paths.
        input_path = Path(args.input).resolve()
        if not input_path.is_file():
            print(f"Error: Input file not found: {args.input}", file=sys.stderr)
            return 1

        try:
            with open(input_path, mode="r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                fieldnames = list(reader.fieldnames or [])
                rows = list(reader)
        except (csv.Error, UnicodeDecodeError) as e:
            print(f"Error reading CSV: {e}", file=sys.stderr)
            return 1

        if not fieldnames:
            print("Error: CSV has no header", file=sys.stderr)
            return 1

        result_fields = ["overall_urgency", "integrity_status", "total_alerts", "audit_hash"]
        out_fields = list(dict.fromkeys(fieldnames + result_fields))
        out_rows = []
        for row_number, r in enumerate(rows, start=2):
            try:
                primary = r.get("primary_metric") or r.get("metric_primary")
                if primary is None:
                    raise ValueError("primary_metric (or metric_primary) is required")
                secondary = r.get("secondary_metric") or r.get("metric_secondary") or 0.0
                payload = SystemTaskPayload(
                    task_id=r.get("task_id") or r.get("case_id") or f"TASK-{row_number}",
                    target_identifier=r.get("target_identifier") or r.get("patient_synthetic_id") or f"SYN-{row_number}",
                    primary_metric=float(primary),
                    secondary_metric=float(secondary),
                    status_descriptor=r.get("status_descriptor") or r.get("status_flag") or "NOMINAL",
                    is_critical_flag=str(
                        r.get("is_critical_flag") or r.get("is_stat") or ""
                    ).strip().lower() in ("true", "1", "yes"),
                )
                dossier = supervisor.process_task(payload)
            except (ValueError, TypeError, SecurityException) as error:
                print(f"Warning: Skipping row {row_number} due to invalid or sensitive data: {type(error).__name__}", file=sys.stderr)
                continue
            row_dict = dict(r)
            row_dict.update(
                overall_urgency=dossier.overall_urgency.value,
                integrity_status=dossier.integrity_status.value,
                total_alerts=dossier.total_alerts,
                audit_hash=dossier.audit_hash,
            )
            out_rows.append(row_dict)

        # Respect explicit output paths; caller controls the output directory.
        output_path = Path(args.output).resolve()
        try:
            with open(output_path, mode="w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=out_fields)
                writer.writeheader()
                writer.writerows(out_rows)
        except OSError as e:
            print(f"Error writing output: {e}", file=sys.stderr)
            return 1
        print(f"Processed {len(out_rows)} records -> {args.output}")
        return 0

    if args.command == "serve":
        try:
            import uvicorn
            from agents.api import app
            print(f"Starting Hfpef Hemodynamic Inpatient Agent API server on http://{args.host}:{args.port}")
            uvicorn.run(app, host=args.host, port=args.port)
            return 0
        except ImportError:
            print("FastAPI / uvicorn not installed. Run 'pip install fastapi uvicorn'", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
