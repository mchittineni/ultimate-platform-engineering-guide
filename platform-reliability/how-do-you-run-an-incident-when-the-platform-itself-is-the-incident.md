---
title: "How do you run an incident when the platform itself is the incident?"
id: 107
category: "Platform Reliability"
difficulty: "Advanced"
tags:
  - platform-engineering
  - platform-reliability
  - interview-questions
---

# How do you run an incident when the platform itself is the incident?

**Short answer:** Assume the tools you would normally use are part of the outage, so incident response needs an independent path: communications that do not depend on the platform, dashboards hosted outside it, a break-glass access route that does not rely on the systems that are down, and runbooks readable without the platform's documentation site. The other half is communication - during a platform incident every team is blocked and, without frequent specific updates, they will each escalate separately.

## Detail

**The circular dependency is the defining problem.** Your status page runs on the platform. Your dashboards query a telemetry pipeline that is part of it. Your runbooks live in the portal. Your break-glass access needs an identity integration that is down. Each of these is fine individually and disastrous together, and the only reliable way to find them is to enumerate the dependencies of your incident response path deliberately - or discover them at 3am.

**What must be independent:**

| Response capability     | Must not depend on                            |
| ----------------------- | --------------------------------------------- |
| Paging and comms        | Your own messaging or the platform's alerting |
| Status communication    | Anything hosted on the platform               |
| Dashboards for triage   | The telemetry pipeline that may be the outage |
| Runbook access          | The documentation portal                      |
| Break-glass access      | The identity integration that may be down     |
| Deploy or rollback path | The reconciler, if that is what is broken     |

The last row is the one people forget: if your only route to production is the GitOps controller and the controller is the problem, you cannot deploy the fix. A documented direct-apply path, used rarely and audited, is the answer.

**Communication is half the job.** Fifty teams are blocked, most cannot tell whether it is them or you, and in the absence of information each will open its own escalation. Frequent, specific updates on a fixed cadence - what is affected, what is not, what to do meanwhile, when the next update comes - reduce the incident's cost more than almost any technical action. "We are investigating" repeated hourly does not; naming which capabilities are degraded and which are unaffected does.

**Tell teams what still works.** During a control-plane outage, running workloads are usually fine - so the correct message is "you cannot deploy, your production traffic is unaffected". Without that, teams assume the worst and start taking unnecessary action, which frequently makes things worse.

**Separate mitigation from repair.** Restore the capability first, understand it afterwards. For a platform this often means removing something: an admission webhook, a new policy, a controller version. A documented and rehearsed way to disable each platform component - especially anything fail-closed in a request path - is worth more than a deep understanding of its failure mode during the incident.

**Expect the reconciler to fight you.** Manual fixes during an incident get reverted by self-healing, sometimes minutes later and confusingly. Suspending reconciliation for the affected scope should be a first-class, documented action rather than something improvised, and the reconciliation of Git back to reality is part of the recovery rather than an afterthought.

**Have a single incident commander even though everyone is affected.** Platform incidents attract many participants because everyone has a stake. Without a commander deciding and a scribe recording, you get parallel uncoordinated changes - which during a platform incident can be actively harmful.

**Retrospect on the response path as well as the cause.** Which of your tools were unavailable, how long triage took because of it, and what you could not see. Fixing the response path is often higher value than fixing the specific cause, because the next platform incident will have a different cause and the same response path.

## Example

```text
An incident where the tooling was part of the outage.

  02:14  admission webhook (policy engine) starts timing out. failurePolicy: Fail.
         -> NO pods can be created anywhere. Any restart or scale event fails.
  02:15  page fires (paging provider is external - independent, correct)
  02:17  on-call opens the platform dashboard
         -> UNAVAILABLE. Grafana runs in the cluster and its pod was rescheduled,
            so it cannot start. First circular dependency hit.
  02:19  falls back to the cloud provider's own metrics console (independent path,
         documented for exactly this case)
  02:22  attempts to read the runbook
         -> the docs portal is also in the cluster. Second circular dependency.
            Cached offline copy in the on-call repo is used instead.
  02:26  MITIGATION, not repair: delete the ValidatingWebhookConfiguration.
         Documented, rehearsed, and it restores pod creation immediately.
         -> policy temporarily unenforced. Accepted, recorded, and time-bounded.
  02:28  pods creating again. Impact ending.
  02:31  status update posted (status page is hosted OUTSIDE the platform)
  03:10  root cause: the webhook was not scaled with the cluster and a node group
         scale-up produced enough concurrent admission requests to exhaust it.
  03:40  webhook scaled, PDB added, timeout reduced, namespaceSelector added to
         exclude kube-system and platform namespaces.
  04:05  webhook configuration restored. Policy enforced again.

  RETROSPECTIVE - two categories, and the second matters more
    CAUSE          webhook not scaled with the cluster; fail-closed on a
                   cluster-wide resource with no self-exclusion
    RESPONSE PATH  dashboards unavailable (12 min lost)
                   runbooks unavailable (4 min lost)
                   -> both moved out of the cluster. The NEXT platform incident
                      will have a different cause and the same response path.
```

```text
The response-path dependency audit - do this before you need it.

  CAPABILITY               DEPENDS ON                    INDEPENDENT?  ACTION
  paging                   external provider              ✓
  incident channel         external messaging              ✓
  status page              was: in-cluster                 ✗ -> moved to external
                                                                static hosting
  triage dashboards        was: in-cluster Grafana          ✗ -> read-only mirror
                                                                outside + cloud
                                                                provider console
                                                                as fallback
  runbooks                 was: docs portal in-cluster      ✗ -> offline copy in
                                                                the on-call repo,
                                                                refreshed in CI
  break-glass access       identity provider                ⚠ -> sealed last-resort
                                                                credential,
                                                                retrieval tested
                                                                quarterly
  deploy / rollback         GitOps reconciler                ✗ -> documented direct
                                                                apply path, audited,
                                                                rehearsed
  suspend reconciliation   reconciler API                    ⚠ -> also achievable by
                                                                scaling the
                                                                controller down;
                                                                both documented

  Every ✗ was found by asking the question, not by having an incident. That is
  the point of doing the audit.
```

```text
The communication that reduces cost most - specific, and says what still works:

  BAD    "We are investigating an issue with the platform." (repeated hourly)

  GOOD   02:31 · Platform incident INC-2291 · degraded
         AFFECTED
           - new pod creation is failing cluster-wide (deploys, scaling, restarts)
         NOT AFFECTED
           - production traffic to running services is unaffected
           - databases, queues, and ingress are healthy
         WHAT TO DO
           - do not restart or scale workloads; they will not come back up
           - hold deploys; queued merges will apply automatically once resolved
         NEXT UPDATE  02:45, or sooner if status changes

  The "NOT AFFECTED" section is what stops fifty teams escalating separately and
  stops people taking harmful action on a false assumption.
```

## Interview tips

- The circular dependency is the whole insight: your dashboards, runbooks, status page, and deploy path may all be part of the outage. Enumerate them deliberately rather than discovering them at 3am.
- The forgotten row is the deploy path - if the reconciler is broken, you cannot ship the fix. A documented, audited direct-apply route is the answer.
- Mitigate before repairing, and note that platform mitigation is often removal - a webhook, a policy, a controller version - which is why rehearsed disable procedures beat deep understanding under pressure.
- The reconciler reverting your manual fix, and suspending reconciliation as a first-class documented action, is a very real detail.
- Communication being half the job, with the "what is NOT affected" section, is the point most candidates miss and it demonstrably reduces incident cost.
- Retrospecting on the response path separately from the cause is the senior close: the next incident will have a different cause and the same response path.

---

[⬅ Back to Platform Reliability](./README.md) · [All topics](../README.md)
