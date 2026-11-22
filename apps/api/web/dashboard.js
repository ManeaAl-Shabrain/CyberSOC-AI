"use strict";

const byId = (id) => document.getElementById(id);
const scenario = byId("scenario");
const runButton = byId("run");
const tokenField = byId("approval-token");
const requestButton = byId("request-approval");
const approvalStatus = byId("approval-status");
let activeCase = null;
let busy = false;
let approvalGeneration = 0;
const foundryButton = byId("foundry-run");
const foundryStatus = byId("foundry-status");
const foundryResults = byId("foundry-results");
let foundryConfigured = false;
let foundryBusy = false;
let foundryDelay = 0;

function element(tag, text, className) {
  const node = document.createElement(tag);
  node.textContent = text;
  if (className) node.className = className;
  return node;
}

function row(title, description) {
  const node = element("div", "");
  node.append(element("p", title, "row-title"), element("p", description, "meta"));
  return node;
}

function list(id, values) {
  byId(id).replaceChildren(...values.map((value) => element("li", value)));
}

function updateApprovalButton() {
  requestButton.disabled = busy || !activeCase ||
    !["high", "critical"].includes(activeCase.severity) || !tokenField.value.trim();
}

async function request(path, options = {}) {
  const response = await fetch(path, { cache: "no-store", ...options });
  if (!response.ok) {
    const result = await response.json().catch(() => ({}));
    throw new Error(typeof result.detail === "string" ? result.detail : "Request failed");
  }
  return response.json();
}

function renderRun(run) {
  activeCase = run.report;
  const report = run.report;
  const flag = byId("severity");
  flag.hidden = !report;
  flag.textContent = report?.severity || "";
  flag.dataset.level = report?.severity || "";
  byId("case-name").textContent = report ? scenario.selectedOptions[0].textContent : "Manual review required";
  byId("summary").textContent = report?.summary || "A workflow stage failed. Review the trace below.";
  byId("evidence-count").textContent = report?.evidence.length ?? 0;
  byId("agent-count").textContent = run.traces.length;
  byId("run-time").textContent = run.traces.reduce((sum, stage) => sum + stage.duration_ms, 0).toFixed(2) + " ms";
  byId("trace-id").textContent = "Trace " + run.trace_id;
  byId("playbook").textContent = report ? "Playbook: " + report.playbook : "";
  byId("findings").replaceChildren(...(report?.findings || []).map(
    (finding) => row(finding.statement, finding.evidence_ids.join(" · "))));
  byId("timeline").replaceChildren(...(report?.timeline || []).map(
    (event) => row(event.event_type.replaceAll("_", " "), event.timestamp + " · " + event.evidence_id)));
  byId("evidence").replaceChildren(...(report?.evidence || []).map(
    (entry) => row(entry.evidence_id + " · " + entry.source, entry.sha256)));
  byId("traces").replaceChildren(...run.traces.map((stage) => {
    const details = element("details", "");
    details.append(element("summary", stage.agent + " · " + stage.status + " · " + stage.duration_ms.toFixed(2) + " ms"));
    details.append(row("Local tools", stage.tools.join(" · ")),
      row("Inputs", stage.input_evidence_ids.join(" · ") || "Synthetic fixture"),
      row("Outputs", stage.output_evidence_ids.join(" · ") || "No evidence references"),
      element("p", "Retries: " + stage.retries + (stage.error_class ? " · " + stage.error_class : ""), "meta"));
    return details;
  }));
  list("recommendations", report?.recommendations || []);
  list("limitations", report?.limitations || []);
}

async function replay() {
  busy = true;
  runButton.disabled = true;
  scenario.disabled = true;
  updateApprovalButton();
  byId("status").textContent = "Replaying synthetic case…";
  try {
    const result = await request("/demo/runs/" + encodeURIComponent(scenario.value));
    renderRun(result);
    byId("status").textContent = result.case_id + (result.report ? " · Ready for analyst review" : " · Workflow needs review");
  } catch (error) {
    activeCase = null;
    byId("status").textContent = error.message;
  } finally {
    busy = false;
    runButton.disabled = false;
    scenario.disabled = false;
    updateApprovalButton();
  }
}

async function updateFoundryStatus() {
  try {
    const status = await request("/demo/foundry/status");
    foundryConfigured = status.configured;
    foundryDelay = status.stage_delay_seconds;
    if (foundryConfigured) foundryButton.textContent = "Run with " + status.deployment;
    foundryStatus.textContent = foundryConfigured
      ? "Ready to request a synthetic replay for the selected scenario."
      : "Foundry is not configured. Local replay is available.";
    foundryButton.disabled = !foundryConfigured || !scenario.value;
  } catch (error) {
    foundryStatus.textContent = error.message;
  }
}

async function replayOnFoundry() {
  const selection = scenario.value;
  const title = scenario.selectedOptions[0].textContent;
  foundryBusy = true;
  foundryButton.disabled = true;
  foundryResults.replaceChildren();
  foundryStatus.textContent = "Running Foundry agents for " + title + "…" +
    (foundryDelay ? " Includes a " + foundryDelay + " s pause between agents." : "");
  try {
    const result = await request("/demo/foundry/runs/" + encodeURIComponent(selection), {
      method: "POST",
      headers: { "X-CyberSOC-Demo": "synthetic-only" },
    });
    const stages = result.stages.map((stage) => row(
      stage.agent + " · " + stage.status + " · " + stage.duration_ms.toFixed(2) + " ms",
      stage.error_class || stage.output_evidence_ids.join(" · ")));
    if (result.status === "manual_review") {
      foundryResults.replaceChildren(...stages);
      foundryStatus.textContent = title + " · Workflow stopped · Manual review required · Trace " + result.trace_id;
      return;
    }
    const report = result.report;
    const evidence = element("details", "");
    evidence.append(element("summary", "Case timeline and evidence"),
      ...report.timeline.map((item) => row(item.event_type, item.timestamp + " · " + item.evidence_id)));
    foundryResults.replaceChildren(
      row("Triage · " + result.triage.severity, result.triage.reason),
      row("Investigation", result.investigation.summary),
      row("Analyst next step", result.investigation.next_step),
      row("Limitations", result.investigation.limitations.join(" · ")),
      evidence,
      ...stages,
    );
    foundryStatus.textContent = title + " · " + result.deployment + " · Analyst review required · Trace " + result.trace_id;
  } catch (error) {
    foundryStatus.textContent = error.message;
  } finally {
    foundryBusy = false;
    foundryButton.disabled = !foundryConfigured || !scenario.value;
  }
}

function authorized(method = "GET") {
  return { method, headers: { Authorization: "Bearer " + tokenField.value.trim() } };
}

async function approvals(path, method = "GET") {
  const generation = ++approvalGeneration;
  const options = authorized(method);
  const readOptions = { headers: options.headers };
  approvalStatus.textContent = "Loading approval records…";
  try {
    if (!tokenField.value.trim()) throw new Error("Enter a local role token.");
    const result = await request(path, options);
    if (generation !== approvalGeneration) return;
    if (path === "/approvals/audit") {
      byId("approval-list").replaceChildren(...result.map((entry) => row(entry.status, entry.actor + " · " + entry.timestamp)));
      approvalStatus.textContent = result.length ? "Audit records loaded." : "No audit records.";
      return;
    }
    const records = method === "POST" ? await request("/approvals", readOptions) : result;
    const session = await request("/approvals/session", readOptions);
    if (generation !== approvalGeneration) return;
    const nodes = records.map((entry) => {
      const node = row(entry.case_id, entry.status.replaceAll("_", " ") + " · " + entry.requester);
      const actions = element("div", "", "action-buttons");
      const commands = entry.status === "awaiting_approval" ? ["approve", "deny"]
        : entry.status === "approved" ? ["simulate"] : [];
      for (const command of session.role === "demo-reviewer" ? commands : []) {
        const button = element("button", command[0].toUpperCase() + command.slice(1), "secondary");
        button.type = "button";
        button.addEventListener("click", () => approvals("/approvals/" + encodeURIComponent(entry.id) + "/" + command, "POST"));
        actions.append(button);
      }
      node.append(actions);
      return node;
    });
    byId("approval-list").replaceChildren(...nodes);
    approvalStatus.textContent = records.length ? "Queue loaded." : "No approval requests.";
  } catch (error) {
    if (generation === approvalGeneration) approvalStatus.textContent = error.message;
  }
}

async function evaluate() {
  const button = byId("evaluate");
  button.disabled = true;
  byId("eval-status").textContent = "Running regression suite…";
  try {
    const result = await request("/demo/evaluation");
    byId("eval-status").textContent = (result.passed ? "Regression gate passed" : "Regression gate failed")
      + " · " + result.cases.length + " synthetic cases · p95 " + result.p95_ms.toFixed(2) + " ms";
    const percent = (value) => Math.round(value * 100) + "%";
    byId("evaluation-results").replaceChildren(
      row("Severity agreement " + percent(result.severity_agreement), "Grounded links " + percent(result.grounded_link_rate)),
      row("Precision " + percent(result.precision), "Recall " + percent(result.recall)),
      ...result.cases.map((item) => row(item.scenario, item.passed ? "Passed · " + item.observed : "Failed")));
  } catch (error) {
    byId("eval-status").textContent = error.message;
  } finally {
    button.disabled = false;
  }
}

runButton.addEventListener("click", replay);
foundryButton.addEventListener("click", replayOnFoundry);
scenario.addEventListener("change", () => {
  activeCase = null;
  updateApprovalButton();
  if (!foundryBusy && foundryConfigured) {
    foundryResults.replaceChildren();
    foundryStatus.textContent = "Ready to request a synthetic replay for the selected scenario.";
  }
});
tokenField.addEventListener("input", () => {
  approvalGeneration += 1;
  byId("approval-list").replaceChildren();
  approvalStatus.textContent = "";
  updateApprovalButton();
});
requestButton.addEventListener("click", () => approvals("/approvals/request/" + encodeURIComponent(scenario.value), "POST"));
byId("refresh-approvals").addEventListener("click", () => approvals("/approvals"));
byId("load-audit").addEventListener("click", () => approvals("/approvals/audit"));
byId("evaluate").addEventListener("click", evaluate);

async function initialize() {
  try {
    const options = await request("/demo/scenarios");
    for (const item of options) {
      const option = element("option", item.title);
      option.value = item.id;
      scenario.append(option);
    }
    await Promise.all([replay(), updateFoundryStatus()]);
  } catch (error) {
    byId("status").textContent = error.message;
  }
}

initialize();
