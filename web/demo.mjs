/**
 * Deterministic browser-only demonstration of the same illustrative decision
 * thresholds used by agents/workers.py. No clinical validation or API calls.
 */
export function evaluateDemo(input) {
  const task = String(input.task_id ?? "").trim();
  const target = String(input.target_identifier ?? "").trim();
  const descriptor = String(input.status_descriptor ?? "").trim();
  const primary = Number(input.primary_metric);
  const secondary = Number(input.secondary_metric);
  const flagged = input.is_critical_flag === true;

  if (!task || !target || task.length > 120 || target.length > 120) {
    throw new Error("Provide synthetic task and target identifiers (1–120 characters).");
  }
  if (descriptor.length > 256 || !Number.isFinite(primary) || !Number.isFinite(secondary)) {
    throw new Error("Enter finite numeric metrics and a descriptor of at most 256 characters.");
  }

  const alerts = [];
  if (primary > 25) {
    alerts.push({
      origin_worker: "InvariantQCWorker",
      urgency: "ELEVATED_RISK",
      summary: "Illustrative primary threshold exceeded",
      technical_details: "Primary metric " + primary + " > 25 (unitless demonstration threshold).",
      actionable_remediation: "Review synthetic input; no clinical action is implied."
    });
  }
  if (flagged || secondary > 12) {
    alerts.push({
      origin_worker: "SafetyEscalationWorker",
      urgency: flagged ? "CRITICAL_STAT_PANIC" : "ELEVATED_RISK",
      summary: "Illustrative safety rule triggered",
      technical_details: "Critical flag: " + flagged + "; secondary metric: " + secondary + ".",
      actionable_remediation: "Review synthetic input; no clinical notification is generated."
    });
  }
  if (["DISCORDANT", "ANOMALY", "MUTANT", "VIOLATION", "FAIL", "REJECT"]
      .some(word => descriptor.toUpperCase().includes(word))) {
    alerts.push({
      origin_worker: "ProtocolConformanceWorker",
      urgency: "ELEVATED_RISK",
      summary: "Illustrative descriptor rule triggered",
      technical_details: "Synthetic descriptor matches a demonstration keyword.",
      actionable_remediation: "Review synthetic descriptor; no test or treatment recommendation."
    });
  }
  const critical = alerts.some(a => a.urgency === "CRITICAL_STAT_PANIC");
  const urgency = critical ? "CRITICAL_STAT_PANIC" :
    alerts.length ? "ELEVATED_RISK" : "ROUTINE";

  return {
    mode: "LOCAL_DEMONSTRATION",
    clinically_validated: false,
    task_id: task,
    target_identifier: target,
    overall_urgency: urgency,
    integrity_status: critical ? "DEMO_CRITICAL_FLAG" :
      alerts.length ? "DEMO_RULE_FLAGGED" : "DEMO_NO_RULES_TRIGGERED",
    total_alerts: alerts.length,
    critical_alerts_count: alerts.filter(a => a.urgency === "CRITICAL_STAT_PANIC").length,
    alerts,
    note: "Synthetic educational demonstration; unitless thresholds are not HFpEF clinical criteria. No actual audit signature, PHI protection, or patient notification."
  };
}

if (typeof document !== "undefined") {
  const form = document.getElementById("audit-form");
  const output = document.getElementById("output-console");
  const announcement = document.getElementById("announcement");
  const download = document.getElementById("download-json");
  const evaluated = document.getElementById("m-tasks");
  const flagged = document.getElementById("m-flagged");
  const critical = document.getElementById("m-critical");
  const status = document.getElementById("m-status");
  let lastResult = null;
  let count = 0;
  let flaggedCount = 0;
  let criticalCount = 0;

  form.addEventListener("submit", event => {
    event.preventDefault();
    try {
      // All processing stays in this browser session; no fetch and no storage.
      const result = evaluateDemo({
        task_id: document.getElementById("task-id").value,
        target_identifier: document.getElementById("target-id").value,
        primary_metric: document.getElementById("primary-metric").value,
        secondary_metric: document.getElementById("secondary-metric").value,
        status_descriptor: document.getElementById("status-descriptor").value,
        is_critical_flag: document.getElementById("is-critical").checked
      });
      lastResult = result;
      count += 1;
      if (result.total_alerts > 0) flaggedCount += 1;
      if (result.critical_alerts_count > 0) criticalCount += 1;
      evaluated.textContent = String(count);
      flagged.textContent = String(flaggedCount);
      critical.textContent = String(criticalCount);
      status.textContent = result.critical_alerts_count ? "Critical demo flag" :
        result.total_alerts ? "Demo rule flagged" : "No demo flags";
      output.textContent = JSON.stringify(result, null, 2);
      announcement.textContent = "Evaluation complete: " + result.total_alerts + " demo alerts.";
      download.disabled = false;
    } catch (error) {
      lastResult = null;
      download.disabled = true;
      announcement.textContent = error.message;
      output.textContent = "Validation error. Correct inputs and re-run.";
    }
  });

  download.addEventListener("click", () => {
    if (!lastResult) return;
    const blob = new Blob([JSON.stringify(lastResult, null, 2) + "\n"], {type: "application/json"});
    const objectUrl = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = objectUrl;
    link.download = "hfpef-demo-result.json";
    link.click();
    URL.revokeObjectURL(objectUrl);
  });
}
