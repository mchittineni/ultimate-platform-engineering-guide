---
title: "How do you turn a compliance framework into automated platform controls?"
id: 144
category: "Policy as Code and Governance"
difficulty: "Advanced"
tags:
  - platform-engineering
  - policy-as-code-and-governance
  - interview-questions
---

# How do you turn a compliance framework into automated platform controls?

**Short answer:** Map each control to a specific, machine-checkable assertion about your systems, implement it where it cannot be bypassed, and emit the evidence as a by-product of enforcement rather than collecting it before an audit. The reframing that matters is that most controls are already satisfied by good platform engineering - the work is in expressing them in the auditor's terms and producing continuous evidence, not in building new mechanisms.

## Detail

**Start by translating, not by building.** A control such as SOC 2 CC6.1 on logical access, or PCI DSS requirements on encryption in transit, is written to be technology-neutral. Your job is to state what would satisfy it in your environment - "every workload authenticates with a federated short-lived identity; no static credentials exist; access is scoped per tenant" - and then check that assertion continuously. Most of these assertions describe things a well-run platform already does.

**Frameworks overlap heavily, so map once and reuse.** SOC 2 and ISO 27001 share the large majority of their substance; GDPR's technical measures overlap both; PCI adds specific requirements on top. Maintain one internal control set mapped to multiple frameworks rather than a separate programme per framework - otherwise you implement the same encryption control three times with three different pieces of evidence. Newer EU regulations join the same map rather than starting new programmes: DORA (applying to financial entities since 17 January 2025), NIS2, and the Cyber Resilience Act, whose vulnerability and incident reporting obligations apply from 11 September 2026, mostly add incident reporting, third-party risk, and SBOM and vulnerability-handling requirements on top of controls the platform already has. See [which frameworks platform teams meet most often](./which-compliance-frameworks-do-platform-teams-meet-most-often.md).

**Implement where it cannot be bypassed.** A control satisfied by a pipeline step is satisfied only for things that went through the pipeline. Admission control, provisioning composition defaults, and cloud organisation policy are the durable enforcement points - and the strongest position is that a non-compliant state is not expressible: if the platform's interface has no field for public access, no team can create a public bucket.

**Evidence as a by-product is the real prize.** The expensive part of compliance is not controls, it is assembling proof, historically by screenshotting consoles the week before an audit. If enforcement emits structured records - every admission decision, every policy evaluation, every access grant, every change with its approver - then the evidence exists continuously and the audit becomes a query. This is the argument that gets platform work funded from a compliance budget.

**Continuous evaluation, not point-in-time.** Auditors increasingly want to know the control operated throughout the period, not that it was configured on the day someone looked. Scheduled evaluation of live state, with results retained for the audit period, answers that directly.

**Exceptions need to be first-class.** Every framework accepts compensating controls and risk acceptance; what it does not accept is an undocumented gap. An exception register with a reason, a compensating control, an owner, an approver, and a review date turns findings into managed risk. Auditors respond well to a documented exception and badly to an undiscovered one.

**Name what cannot be automated.** Personnel controls, training, vendor due diligence, physical security, and policy documents are real controls that no admission webhook satisfies. Claiming full automation damages credibility; being precise about the boundary strengthens it.

**Involve the auditor in the mapping early.** Whether your evidence format is acceptable is a question with an answer, and finding out in advance is far cheaper than rebuilding evidence collection after a first audit.

## Example

```text
One internal control set, mapped to several frameworks - implemented once,
evidenced once.

CONTROL  encryption of data at rest
  frameworks   SOC 2 CC6.7 · ISO 27001 A.8.24 · PCI DSS 3 · GDPR Art.32
  assertion    every provisioned datastore and volume has encryption enabled
               with a managed key
  enforced     provisioning composition sets it unconditionally; the platform
               interface has NO field to disable it -> non-compliance is not
               expressible
  evidence     daily inventory of every datastore with its encryption state and
               key reference, retained 13 months
  automated    fully

CONTROL  logical access is least-privilege and individually attributable
  frameworks   SOC 2 CC6.1/CC6.2 · ISO 27001 A.5.15 · PCI DSS 7, 8
  assertion    no standing privileged access; workloads use federated short-lived
               identity; every privileged action attributable to a person
  enforced     no static credentials admitted; break-glass is time-bound and
               session-recorded; RBAC generated per tenant
  evidence     break-glass activation log with reason, duration, and commands;
               quarterly audit of trust policies and standing privileges
  automated    fully, except the quarterly access review sign-off (human)

CONTROL  changes are authorised, tested, and traceable
  frameworks   SOC 2 CC8.1 · ISO 27001 A.8.32
  assertion    every production change is a reviewed commit with a green pipeline
  enforced     branch protection + required review; pull-based deploy so nothing
               reaches production outside Git
  evidence     the Git history IS the change log - author, reviewer, timestamp,
               diff, pipeline result, deploy record
  automated    fully. This one is free if you already do GitOps.

CONTROL  vulnerabilities are identified and remediated on a defined timeline
  frameworks   SOC 2 CC7.1 · ISO 27001 A.8.8 · PCI DSS 6, 11
  assertion    all deployed images have an SBOM, are scanned continuously, and
               criticals are remediated within the stated window
  enforced     admission requires a signed image with provenance and an SBOM
  evidence     SBOM index, scan history, remediation timings per finding
  automated    mostly - the remediation SLA needs the residual register

CONTROL  security awareness training completed annually
  frameworks   SOC 2 CC1.4 · ISO 27001 A.6.3
  automated    NOT AUTOMATABLE by the platform. Owned by People/Security.
               Say so plainly rather than implying coverage.
```

```yaml
# Control as code, carrying its own framework mapping and evidence definition.
# The mapping in the annotation is what makes the audit a query.
apiVersion: platform.example.com/v1
kind: Control
metadata:
  name: encryption-at-rest
  annotations:
    compliance.example.com/soc2: "CC6.7"
    compliance.example.com/iso27001: "A.8.24"
    compliance.example.com/pci-dss: "3.5"
    compliance.example.com/gdpr: "Art.32(1)(a)"
spec:
  assertion: "All provisioned datastores and volumes are encrypted with a managed key."
  enforcement:
    - type: composition-default # not expressible otherwise
      ref: compositions/postgres
      note: "storageEncrypted: true is set unconditionally; no claim field exposes it"
    - type: admission-policy
      ref: policies/require-encrypted-storageclass
    - type: cloud-org-policy
      ref: scp/deny-unencrypted-rds
  evidence:
    query: platform inventory datastores --fields name,encrypted,kmsKeyId,tenant
    schedule: daily
    retention: 13months # audit period + margin
  owner: group:platform-security
```

```text
The audit interaction this design produces:

  auditor  "Show me that all production databases were encrypted throughout the
            period, not just today."

  before   screenshot each console, per account, per region. Days of work, and
           it only ever proves the state on the day you looked.

  after    $ platform compliance evidence --control encryption-at-rest \
             --from 2025-08-01 --to 2026-07-31
             365 daily inventories, 0 findings
             plus: the SCP that makes an unencrypted instance impossible to
             create, and the composition that has no field to disable it

  The strongest evidence is not the log showing compliance - it is demonstrating
  that the non-compliant state cannot be expressed.
```

## Interview tips

- Lead with the reframe: most controls are already satisfied by good platform engineering, and the work is translation plus continuous evidence rather than new mechanisms.
- "Evidence as a by-product of enforcement" is the sentence that lands, and it is also the argument that gets platform work funded from a compliance budget.
- Map once to multiple frameworks. Naming the SOC 2 and ISO 27001 overlap shows you have run more than one programme.
- The strongest form of a control is that non-compliance is not expressible - no field exists to disable encryption. That is a better answer than a policy that rejects it.
- Continuous evaluation over point-in-time is what auditors increasingly ask for, and it is the difference between a screenshot and a year of daily inventories.
- Be explicit about what the platform cannot automate - training, vendor due diligence, physical security. Precision about the boundary is more credible than claiming full coverage.
- The exception register with compensating controls and approvers is what converts a gap into managed risk, which is what auditors actually accept.

---

[⬅ Back to Policy as Code and Governance](./README.md) · [All topics](../README.md)
