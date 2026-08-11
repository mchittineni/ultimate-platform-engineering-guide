---
title: "How do you design break-glass access to production?"
id: 72
category: "Platform Security"
difficulty: "Advanced"
tags:
  - platform-engineering
  - platform-security
  - interview-questions
---

# How do you design break-glass access to production?

**Short answer:** Make it exist, make it fast, make it loud. A time-bound elevated role that an engineer can activate themselves with a stated reason, which alerts a channel immediately, records every action in a session log, and expires automatically - reviewed afterwards rather than approved beforehand. The design goal is that nobody ever needs a standing privileged account, because standing access is the thing you are trying to eliminate.

## Detail

**Why it must exist.** Some incidents cannot be resolved through the platform's normal interfaces - the platform itself is broken, or the situation is genuinely novel. If there is no legitimate path to elevated access, engineers will create illegitimate ones: a personal access key, a shared account, a permanently elevated role "just in case". Those are far more dangerous than a well-designed break-glass, because they are invisible and permanent.

**Speed is a security property here, not a compromise of it.** If activating break-glass takes twenty minutes of approval chasing during an outage, people will route around it. Self-service activation with immediate notification and after-the-fact review is both faster and more auditable than a pre-approval gate that gets bypassed. This trade - detection instead of prevention - is the core design decision, and it is the right one for a small number of trusted engineers under time pressure.

**What the mechanism needs:**

- **Self-service activation** with a mandatory reason and an incident reference, in seconds.
- **Time-bound by construction.** The credential expires - typically in under an hour - rather than relying on someone remembering to revoke it. Extension requires a fresh activation and a fresh alert.
- **Loud notification.** A message to a channel with who, why, which incident, and for how long, plus a page to a security on-call for the highest tiers. Someone should notice every activation without looking for it.
- **Session recording.** Every command and API call attributed to the human, not to a shared role. Without this you know access was granted and nothing about what was done.
- **Scoped, not omnipotent.** Several tiers - read-only diagnostics, workload restart, and full administrative - so the common case does not require the strongest role.
- **Mandatory review.** Every activation reviewed within a working day: was it necessary, could a platform capability have avoided it, was anything changed that must be reconciled back into Git.

**Read-only diagnostics should barely be break-glass at all.** A large share of activations are just "I need to look at something I cannot see". Making deep read access routinely available - logs, describes, resource state - removes most of the pressure on the privileged path and shrinks the interesting activations to a reviewable number.

**Reconcile afterwards, always.** Manual changes made under break-glass will be reverted by the reconciler or will persist as undeclared drift. The review must ask what changed and require it to be either committed to Git or removed. This is the step most often skipped, and it is how incident-time fixes become permanent undocumented differences.

**The frequency is a platform metric.** Regular activations for the same reason indicate a missing capability, not a discipline problem. If four engineers broke glass this month to restart a stuck workload, the platform should expose a supported way to restart a stuck workload.

**Do not let it depend on the systems it may need to fix.** If break-glass requires your identity provider, and the identity provider integration is the outage, you have no path. Keep a genuinely last-resort mechanism - a sealed credential with a documented retrieval procedure, tested periodically - separate from the everyday path.

## Example

```yaml
# Tiered roles, so the common case does not need the strongest one.
apiVersion: platform.example.com/v1
kind: BreakGlassPolicy
metadata: { name: production }
spec:
  tiers:
    - name: diagnose # ~80% of real need
      grants: [read-all, logs-read, exec-readonly]
      duration: 4h
      approval: self-service
      notify: ["#platform-access"]
      review: weekly-batch # low risk, reviewed in aggregate

    - name: operate
      grants: [workload-restart, scale, cordon-node, suspend-reconciliation]
      duration: 1h
      approval: self-service
      notify: ["#platform-access", "#incident"]
      review: next-working-day

    - name: administer # rare, and it should feel rare
      grants: [cluster-admin]
      duration: 30m
      approval: self-service # speed matters more than a gate that gets bypassed
      notify: ["#platform-access", "#security", "pagerduty:security-oncall"]
      review: next-working-day-mandatory

  always:
    requireReason: true
    requireIncidentRef: true
    sessionRecording: true # attributed to the human, not a shared role
    expiry: hard # credential expires; no manual revocation needed
    reconcileCheck: true # review must resolve any manual change
```

```text
An activation, end to end:

  $ platform break-glass administer --incident INC-2291 \
      --reason "argocd controller crashlooping; cannot suspend app via API"

    ⚠  Tier: administer. Duration 30m. Expires 02:47Z.
    ⚠  Notified: #platform-access, #security, paged security-oncall
    ⚠  Session recording active. Review required by 2026-08-12 17:00.
    ✓  Credentials issued (30m, no refresh)

  ... engineer works; every command recorded ...

  02:47Z  credential expired automatically. No revocation step, nothing to forget.

  NEXT DAY REVIEW
    activated by      bob            incident  INC-2291
    tier              administer     duration  used 19m of 30m
    commands          41 recorded

    ✓ necessary?      yes - the Argo CD API was unavailable, so suspending the
                      application through the platform was genuinely impossible
    ✗ avoidable?      PARTLY. 12 of 41 commands were read-only diagnosis that the
                      `diagnose` tier would have covered. Bob escalated straight
                      to `administer` because he was not sure which tier he needed.
                      -> platform action: better tier guidance in the CLI
    ✗ reconcile?      YES - a DaemonSet was created manually to capture traffic.
                      Still running. -> remove it, or commit it to the bundle.
                      Ticket raised; drift report already flagged it.
```

```text
The metric that turns break-glass into product feedback:

  $ platform break-glass report --quarter 2026-Q3

  ACTIVATIONS BY REASON
    restart a stuck workload .......... 14   <-- MISSING CAPABILITY. Fourteen
                                              activations for something the
                                              platform should simply support.
    inspect logs not in the pipeline ..  9   <-- log routing gap
    suspend reconciliation ............  6   <-- should be a first-class,
                                              non-privileged operation
    genuinely novel situations .........  3   <-- this is the number that should
                                              remain; the rest are roadmap items
    ------------------------------------------
    total ............................. 32

  Target after the roadmap items ship: fewer than 5 per quarter, all novel.
  Frequency is not a discipline metric. It is a gap list.
```

## Interview tips

- "Make it exist, make it fast, make it loud" is a strong opening, followed immediately by the reason: without a legitimate path, engineers create illegitimate standing access, which is worse.
- Frame self-service activation with after-the-fact review as a deliberate choice of detection over prevention. Defending that trade-off confidently is the senior signal; an approval gate that gets bypassed under pressure provides neither speed nor control.
- Expiry by construction rather than manual revocation is a small, important design detail.
- Tiering, with read-only diagnostics being routinely available, is what shrinks activations to a reviewable number. Most candidates propose a single all-powerful role.
- The reconcile-afterwards step is the one most often skipped, and it is how incident fixes become permanent undocumented drift.
- Treating activation frequency as a gap list rather than a discipline metric is the strongest close - fourteen activations to restart a workload is a roadmap item.
- The circular-dependency point - break-glass that needs the identity provider that is down - deserves a genuinely last-resort mechanism that is tested periodically.

---

[⬅ Back to Platform Security](./README.md) · [All topics](../README.md)
