---
title: "How do you handle policy exceptions without eroding the guardrails?"
id: 78
category: "Policy as Code and Governance"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - policy-as-code-and-governance
  - interview-questions
---

# How do you handle policy exceptions without eroding the guardrails?

**Short answer:** Make exceptions explicit, narrow, owned, expiring, and visible - a declared object scoped to one policy and one resource, with a reason, an approver, a compensating control, and a review date. Exceptions that are granted informally, apply broadly, or never expire are how a policy set decays into decoration. The health metric is not the number of exceptions but how many have expired without review.

## Detail

**Exceptions are necessary, and refusing them is worse than granting them.** Every policy set meets a legitimate case it did not anticipate: a workload that genuinely needs a privileged capability, a vendor image that cannot carry your labels, a migration that must temporarily violate a rule. If there is no supported route, people find unsupported ones - a namespace excluded from policy entirely, an annotation someone added, a policy quietly relaxed for everyone. Those are far more damaging than a documented exception because they are invisible and unbounded.

**What every exception must carry:**

| Field                | Why                                                         |
| -------------------- | ----------------------------------------------------------- |
| Policy               | One policy - never "exempt from all policy"                 |
| Scope                | Specific resources, not a whole namespace                   |
| Reason               | What is genuinely impossible, not "we do not have time yet" |
| Compensating control | What reduces the risk in the meantime                       |
| Owner                | A named person who will be contacted at review              |
| Approver             | Who accepted the risk, and at what level                    |
| Expiry               | A date after which it stops applying                        |

**Narrow the scope aggressively.** Excluding a namespace from a policy exempts everything in it now and everything created in it later, including workloads nobody has thought about. Exempting a named resource for a named policy is bounded. This is the difference between a hole and a door.

**Expiry must be enforced by the mechanism, not by a calendar reminder.** If the exception object carries a date and the controller stops honouring it after that date, exceptions cannot rot. If expiry is a note in a spreadsheet, most of them will still be there in three years. Renewal should be possible and should require the same approval as the original - that is the review.

**Compensating controls are what make an exception defensible.** "This workload needs a privileged capability" is a gap. "This workload needs a privileged capability; it runs on a dedicated node pool, has no network egress, and is reviewed monthly" is managed risk. Requiring the field forces the conversation, and it is also exactly what an auditor wants to see.

**Match the approval level to the risk.** A missing owner label needs a team lead. A privileged container in a PCI-scoped cluster needs security sign-off. A single approval path for all exceptions is either too heavy for the common case or too light for the serious one.

**Review the register for patterns.** Fifteen exceptions to the same policy is not fifteen exceptional cases - it is a policy that is wrong, or a missing platform capability. This is the same product-feedback loop as escape hatches from golden paths: the exceptions tell you where your rules do not fit reality.

**Make it visible.** The register should be queryable and reported - by team, by policy, by expiry. An exception nobody can see is indistinguishable from an unenforced policy, which defeats the point of having the policy.

## Example

```yaml
# One policy, one resource, with everything needed to defend it later.
apiVersion: platform.example.com/v1
kind: PolicyException
metadata: { name: ml-inference-privileged-gpu }
spec:
  policy: disallow-privileged-containers # ONE policy, never a blanket exemption
  scope:
    namespace: team-ml
    resources: # named resources, not the whole namespace
      - { kind: Deployment, name: gpu-inference }
  reason: >
    The NVIDIA device plugin requires SYS_ADMIN to expose GPU devices to the
    container. No unprivileged path exists with the current driver version.
  compensatingControls:
    - "Runs only on the dedicated `gpu` node pool, tainted and isolated"
    - "NetworkPolicy: no egress except the model bucket and the telemetry collector"
    - "Image pinned by digest, signed, provenance verified"
    - "No secrets mounted; workload identity scoped to read-only model access"
  owner: alice@example.com
  approvedBy: security-lead@example.com
  approvalLevel: security # matched to the risk, not a single global path
  created: 2026-05-02
  expires: 2026-11-02 # ENFORCED by the controller, not a reminder
  reviewNotes: >
    Revisit when the driver's unprivileged device path ships (tracked in PLAT-882).
```

```text
The register, reported monthly. The last two sections are the ones that matter.

  $ platform exceptions report

  ACTIVE BY POLICY
    disallow-privileged-containers ...... 3   (all GPU/device-plugin related)
    require-resource-requests ........... 9   <-- PATTERN. See below.
    require-signed-images ............... 4   (all third-party vendor images)
    require-owner-label ................. 1
    -------------------------------------------
    total ............................... 17

  PATTERN ANALYSIS - exceptions as product feedback
    require-resource-requests: 9 exceptions, 7 of them for the same reason -
    memory-heavy JVM workloads where our LimitRange default causes an OOM.
    -> This is not 9 exceptional cases. It is a wrong default.
       Action: add a `jvm` size class with appropriate defaults. Expected to
       close 7 of the 9 without any team doing anything.

    require-signed-images: 4 exceptions, all vendor images with no signing.
    -> Not fixable by us. Keep as long-lived exceptions with vendor escalation
       recorded; review annually rather than quarterly.

  HEALTH - the metric that actually matters
    expired but still present .............. 2   <-- FAILURE. The controller
                                                   should have stopped honouring
                                                   these. Investigate the bug.
    expiring within 30 days ................ 4   -> renewal conversations opened
    scoped to a whole namespace ............ 0   ✓ (was 6 a year ago)
    missing a compensating control .......... 0   ✓
    missing a named owner ................... 0   ✓

  Count of exceptions is not the health metric. Expired-but-honoured is.
```

## Interview tips

- Say first that exceptions must exist, and that refusing them produces worse outcomes - namespace-wide exclusions and quietly relaxed policies that nobody can see.
- The seven required fields are the substance. Expiry and compensating control are the two that most distinguish a real process from a rubber stamp.
- "Enforced expiry, not a calendar reminder" is the mechanism point. If the controller stops honouring the exception on the date, exceptions cannot rot.
- Narrow scope aggressively - a named resource for a named policy, never a whole namespace. The hole-versus-door framing is memorable.
- Matching approval level to risk shows judgement; a single approval path is either too heavy or too light.
- Pattern analysis is the senior move: nine exceptions to one policy means the policy or the default is wrong, and fixing it closes seven of them without asking anyone.
- The health metric being "expired but still honoured" rather than the count is a sharp, defensible position and a good close.

---

[⬅ Back to Policy as Code and Governance](./README.md) · [All topics](../README.md)
