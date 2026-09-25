---
title: "What is the difference between preventive and detective controls?"
id: 135
category: "Policy as Code and Governance"
difficulty: "Beginner"
tags:
  - platform-engineering
  - policy-as-code-and-governance
  - interview-questions
---

# What is the difference between preventive and detective controls?

**Short answer:** A preventive control stops a bad state from being created, such as an admission policy that rejects a privileged container or a cloud organisation policy that denies unencrypted storage. A detective control finds a bad state after it exists, such as a scheduled scan of live resources, a drift report, or an alert on an audit log event. You need both, because prevention only sees changes that pass through it, and detection is the only way to find what slipped past, predates the rule, or drifted afterwards.

## Detail

**The terms come from security and audit, and platform engineers are expected to use them.** Auditors classify every control as preventive, detective, or corrective (the last one fixes the problem once it is found). When an interviewer asks this question they are checking whether you can describe your platform controls in the language a security or compliance team uses.

**Preventive controls act before the change lands.** Examples on a typical platform:

- Kubernetes admission policies (ValidatingAdmissionPolicy, Kyverno, Gatekeeper) rejecting non-compliant objects.
- Cloud organisation guardrails: AWS service control policies and resource control policies, Azure Policy with a `deny` effect, Google Cloud organisation policy constraints.
- Branch protection that makes a reviewed pull request the only route to `main`.
- Self-service templates that simply have no field for the unsafe option.

**Detective controls act after the fact.** Examples:

- Background or audit scans that evaluate every existing resource against current policy.
- Cloud posture tools (AWS Config rules, Azure Policy compliance results, Security Command Center findings).
- GitOps drift detection: live state no longer matches Git.
- Alerts on audit log events, such as a break-glass role being assumed, or a new public IP.
- Vulnerability scanning of running images, because a CVE published today affects an image that was clean at deploy time.

**Why prevention alone is never enough.** Prevention has three blind spots. It only sees changes that pass through it: a resource created before the policy existed, or through a path the control does not cover (a console click in an account outside the organisation policy, a direct database change), is invisible to it. It only checks the rules as they are today, so tightening a rule does nothing to what is already running. And the world changes underneath it: an image that passed admission becomes vulnerable next week without anyone touching it.

**Why detection alone is not enough either.** A detective control tells you the bucket was public, not that it never became public. For high-impact states (public data, privileged access, unencrypted regulated data) the time between the bad state appearing and someone fixing it is exposure, and a report nobody reads is exposure that never ends. Detection is only as good as the process that acts on its findings, which is why detective controls need an owner, a severity, and a fix-by time.

**How they fit together.** The usual pattern is the same rule implemented twice: preventive at the enforcement point for new changes, and detective as a scheduled evaluation of everything that exists. Many policy engines do both from one definition. Kyverno and Gatekeeper evaluate at admission and also run background audits of existing resources, and a native ValidatingAdmissionPolicy binding can `Deny` new objects while an audit tool reports on old ones. Findings from the detective side then feed a corrective step: an automated pull request, a mutation on next deploy, or a ticket to the owning team.

**Who this serves.** For application teams, preventive controls should feel like fast, clear feedback on their own change. Detective findings should arrive routed to the owning team with the fix attached, not as a monthly spreadsheet from security. For auditors, the pair answers two questions: "can a bad state be created?" (preventive) and "how would you know if one existed?" (detective).

**The trade-off.** Preventive controls are in the critical path. A buggy or unavailable admission webhook can block every deploy, so they must be tested, rolled out carefully, and kept narrow. Detective controls are safe to run broadly but generate findings that need triage, and a noisy one gets ignored. A reasonable rule: prevent what is high impact and clearly defined, detect everything else, and promote a detective rule to preventive once its findings are near zero.

## Example

```text
One rule - "no storage bucket may allow public access" - as a layered set of controls
on AWS. Each layer covers a gap in the one above it.

PREVENTIVE
  self-service template   the bucket module has no "public" input at all
  admission / CI          Conftest on the Terraform plan fails a public ACL,
                          with the fix in the message
  organisation guardrail  an SCP denies s3:PutBucketPublicAccessBlock changes
                          outside the platform role; S3 Block Public Access
                          is enforced account-wide

DETECTIVE
  posture scan            an AWS Config rule reports any bucket whose public
                          access block is not fully enabled - catches buckets
                          created before the guardrail existed
  audit log alert         an alert on changes to bucket policies or public
                          access settings, routed to the owning team's channel

CORRECTIVE
  automated remediation   a finding on a non-exempt bucket re-applies the block
                          and opens a ticket with the owner, so a human knows
                          it happened

Auditor question            Answered by
  "Can one be created?"     the preventive layers
  "Would you know?"         the detective layers, plus their alert history
  "What did you do?"        the corrective record
```

## Interview tips

- Define both in one sentence each: preventive stops the bad state being created, detective finds it once it exists. Then add "corrective" to show you know the full audit vocabulary.
- Give the three blind spots of prevention: things created before the rule, paths the control does not cover, and things that change without anyone touching them, such as new CVEs.
- The strongest point is that you implement the same rule both ways, often from one policy definition, with admission for new changes and a background audit for existing state.
- Say that a detective control without an owner and a fix-by time is just a report. Findings need routing to the team that can fix them.
- Mention that preventive controls are in the critical path and can cause outages, which is why you roll them out in audit mode first. See [audit mode versus enforce mode](./what-is-the-difference-between-audit-mode-and-enforce-mode-for-a-policy.md).
- For drift as a detective control, see [how a platform detects configuration drift](../gitops-and-continuous-delivery/what-is-configuration-drift-and-how-does-a-platform-detect-it.md).

---

[⬅ Back to Policy as Code and Governance](./README.md) · [All topics](../README.md)
