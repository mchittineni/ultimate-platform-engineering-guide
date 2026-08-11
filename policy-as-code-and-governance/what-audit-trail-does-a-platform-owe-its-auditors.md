---
title: "What audit trail does a platform owe its auditors?"
id: 79
category: "Policy as Code and Governance"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - policy-as-code-and-governance
  - interview-questions
---

# What audit trail does a platform owe its auditors?

**Short answer:** An attributable, tamper-resistant record of who changed what, when, with whose approval - covering code changes, infrastructure changes, access grants, privileged sessions, policy decisions, and configuration changes that alter behaviour without a deploy. The two gaps almost every platform has are attribution of actions taken by automation on a human's behalf, and changes that bypass the deployment path entirely, such as a feature flag flip.

## Detail

**What the record has to answer.** Not "do we have logs" but specific questions: who deployed this version to production and who approved it; who had privileged access last quarter and what did they do; what changed in this account in the last month and was it authorised; why does this resource differ from its declared state. If your logging cannot answer those, it is telemetry rather than an audit trail.

**The sources, and what each covers:**

| Source                   | Covers                                               |
| ------------------------ | ---------------------------------------------------- |
| Git history              | Code and declared configuration, author, reviewer    |
| CI/CD records            | What was built, tested, and deployed, and by whom    |
| Kubernetes audit log     | Every API request, its identity, and the object diff |
| Cloud audit log          | Infrastructure changes and API calls                 |
| Identity provider logs   | Authentication, group membership changes             |
| Break-glass session logs | Privileged commands attributed to a person           |
| Policy decision logs     | What was admitted or rejected, and why               |
| Flag change log          | Behaviour changes that did not go through a deploy   |

**Attribution through automation is the hard part, and the most commonly missing.** The Kubernetes audit log shows the GitOps controller applied a change; the cloud audit log shows the provisioning controller created a database. Neither names the human. The fix is to correlate: the controller's action carries the commit it came from, the commit has an author and a reviewer, and the record joins them. Without that join, every production change is attributed to a service account, which satisfies nobody.

**Changes outside the deployment path are the other systematic gap.** A feature flag flip changes production behaviour with no commit, no pipeline, and no deploy record. So can a configuration change in a vendor console, a manual scaling action, or a runtime toggle. Each of these needs its own recorded change event, and it should reach the same change feed as deployments - otherwise your change record is systematically missing your fastest-acting changes.

**Approval must be part of the record, not a separate system.** A pull request with a required review gives you the approver, the timestamp, and what they approved, all in one artefact. Approvals recorded in a ticketing system and linked by hand tend not to reconcile, and reconciling them is exactly what an audit asks you to do.

**Tamper resistance matters for the trail itself.** Ship audit records to a destination the operators of the audited systems cannot modify - a separate account, append-only storage, with its own access controls and retention. An audit log a platform administrator can edit is weak evidence, and this is a finding auditors look for specifically.

**Retention should be set by the audit period plus margin, and enforced.** Thirteen months is a common choice for an annual audit. Set it once at the destination rather than trusting per-source configuration, and be aware that verbose Kubernetes audit logging is expensive - which is why the audit policy should be tuned to record what matters rather than everything.

**Make it queryable, because unqueryable evidence has no value.** The test is whether you can answer an auditor's sampled question - "show me the authorisation for this specific change on this date" - in minutes. If assembling evidence takes days, the trail exists but the capability does not.

## Example

```yaml
# Kubernetes audit policy - tuned, because logging everything at RequestResponse
# is expensive and mostly noise.
apiVersion: audit.k8s.io/v1
kind: Policy
omitStages: ["RequestReceived"]
rules:
  # Full request and response for anything security-relevant
  - level: RequestResponse
    resources:
      - { group: "", resources: ["secrets", "serviceaccounts"] }
      - { group: "rbac.authorization.k8s.io", resources: ["*"] }
      - { group: "platform.example.com", resources: ["*"] }
  # Metadata is enough for routine workload changes
  - level: Metadata
    verbs: ["create", "update", "patch", "delete"]
    resources:
      - { group: "apps", resources: ["deployments", "statefulsets", "daemonsets"] }
  # Drop the high-volume, low-value traffic
  - level: None
    users: ["system:kube-scheduler", "system:kube-controller-manager"]
  - level: None
    resources: [{ group: "", resources: ["events", "endpoints"] }]
```

```text
The attribution join - the gap most platforms have. Neither log alone names a human.

  RAW (what the logs say on their own)
    k8s audit    user=system:serviceaccount:argocd:application-controller
                 verb=patch  resource=deployments/checkout  ns=team-payments
                 -> attributed to a service account. Useless for an audit.
    cloud audit  principal=arn:...:role/crossplane-provider-aws
                 action=rds:ModifyDBInstance  resource=checkout-db
                 -> same problem.

  JOINED (correlating through the commit the controller acted on)
    change      deployment of checkout 1.4.2 to production
    commit      abc123def  "fix: correct VAT rounding for EU orders"
    author      alice@example.com          (wrote the change)
    reviewer    dave@example.com           (approved it, 2026-08-10T09:12Z)
    pipeline    run 4821 - tests pass, image signed, provenance attested
    promoted by bot, approved by  carol@example.com  (production environment gate)
    applied     2026-08-11T09:14Z by argocd application-controller
    diff        image sha256:4a1e... -> sha256:9f2c...

  Now it answers "who changed production and who approved it". The controller is
  the mechanism; the humans are named.
```

```text
The systematic gap: changes that never touch the deployment path.

  $ platform changes feed --production --last 24h

  09:14  DEPLOY   checkout 1.4.2          alice (author) / dave (review) / carol (approve)
  11:02  INFRA    checkout-db resized     bob   / PR #1204 / carol (approve)
  13:47  FLAG     checkout-new-pricing    alice   0% -> 5%     <-- no commit, no
                                                                  pipeline, no deploy.
                                                                  Would be INVISIBLE
                                                                  without a flag
                                                                  change log.
  14:20  ACCESS   break-glass administer  bob   INC-2291, 19m, 41 commands recorded
  15:05  MANUAL   deploy/search scaled    eve   via kubectl  <-- reverted by
                                                                 selfHeal at 15:07;
                                                                 recorded anyway
  16:30  POLICY   require-resource-requests -> Enforce   platform-team / PR #1211

  One feed, six sources. The 13:47 row is the one that is systematically missing
  in most organisations, and it is a production behaviour change made in seconds.
```

## Interview tips

- Reframe from "do we have logs" to the specific questions the trail must answer. That immediately distinguishes an audit trail from telemetry.
- The attribution-through-automation gap is the highest-value point. The audit log naming a service account is useless, and the fix is joining through the commit to its author and reviewer.
- Flag flips as changes outside the deployment path is the second key gap, and it is the one that makes your change record systematically incomplete for your fastest changes.
- Approval in the same artefact as the change - a reviewed pull request - avoids the reconciliation exercise that separate ticketing systems create.
- Tamper resistance: ship to a destination the audited operators cannot modify. Auditors look for this specifically.
- Mention tuning the audit policy, since logging everything at full fidelity is genuinely expensive. It shows you have operated this rather than configured it once.
- The closing test is time-to-answer for a sampled question. Evidence that takes days to assemble exists but is not a capability.

---

[⬅ Back to Policy as Code and Governance](./README.md) · [All topics](../README.md)
