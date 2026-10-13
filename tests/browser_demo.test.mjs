import test from "node:test";
import assert from "node:assert/strict";
import { evaluateDemo } from "../web/demo.mjs";

const payload = {
  task_id: "SYN-1",
  target_identifier: "SYN-2",
  primary_metric: 10,
  secondary_metric: 2,
  status_descriptor: "NORMAL",
  is_critical_flag: false
};

test("unflagged demo input does not create alerts", () => {
  const res = evaluateDemo(payload);
  assert.equal(res.total_alerts, 0);
  assert.equal(res.overall_urgency, "ROUTINE");
  assert.equal(res.clinically_validated, false);
  assert.ok(!("audit_hash" in res));
});

test("primary, secondary and descriptor rules match backend demonstration", () => {
  const res = evaluateDemo({...payload, primary_metric: 26, secondary_metric: 13, status_descriptor: "DISCORDANT"});
  assert.equal(res.total_alerts, 3);
  assert.equal(res.overall_urgency, "ELEVATED_RISK");
});

test("critical flag alone increases demo urgency", () => {
  const res = evaluateDemo({...payload, is_critical_flag: true});
  assert.equal(res.critical_alerts_count, 1);
  assert.equal(res.overall_urgency, "CRITICAL_STAT_PANIC");
});

test("boundaries are strict greater-than, not greater-or-equal", () => {
  const res = evaluateDemo({...payload, primary_metric: 25, secondary_metric: 12});
  assert.equal(res.total_alerts, 0);
});

test("nonfinite and missing metrics are rejected", () => {
  assert.throws(() => evaluateDemo({...payload, primary_metric: "Infinity"}), /finite/);
  assert.throws(() => evaluateDemo({...payload, secondary_metric: "NaN"}), /finite/);
  assert.throws(() => evaluateDemo({...payload, task_id: ""}), /synthetic/);
});
