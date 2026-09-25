---
title: "Which compliance frameworks do platform teams meet most often?"
id: 137
category: "Policy as Code and Governance"
difficulty: "Beginner"
tags:
  - platform-engineering
  - policy-as-code-and-governance
  - interview-questions
---

# Which compliance frameworks do platform teams meet most often?

**Short answer:** SOC 2 and ISO/IEC 27001 are the two almost every platform team meets, because customers ask for them. PCI DSS applies wherever card data is handled, HIPAA for US health data, and GDPR wherever EU personal data is processed. Technical baselines such as the CIS Benchmarks sit underneath all of them. In the EU, newer regulations (DORA for financial services, NIS2 for essential and important entities, and the Cyber Resilience Act for products with digital elements) increasingly reach the platform too. The frameworks overlap heavily, so a platform maps its controls once and reuses the evidence across them.

## Detail

**Frameworks, standards, and laws are different kinds of thing.** SOC 2 is an attestation: an independent auditor reports on your controls against the AICPA Trust Services Criteria. ISO/IEC 27001 is a certifiable standard for an information security management system. PCI DSS is an industry standard enforced through card-scheme contracts. GDPR, HIPAA, DORA, NIS2, and the Cyber Resilience Act are laws or regulations. CIS Benchmarks are voluntary technical configuration guides. In an interview, getting these categories right is a quick signal that you have actually worked with a compliance team.

**The ones you will meet, and what they ask of a platform:**

| Framework                | What it is                                                                      | What lands on the platform                                                        |
| ------------------------ | ------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| SOC 2                    | Auditor's report on controls; Type II covers a period, usually a year           | Access control, change management, logging, evidence that controls ran all period |
| ISO/IEC 27001:2022       | Certifiable management system; 93 Annex A controls in 4 themes                  | Same technical controls as SOC 2, plus documented risk treatment                  |
| PCI DSS v4.0.1           | Card industry standard; future-dated requirements mandatory since 31 March 2025 | Segmentation of the cardholder data environment, encryption, logging, patching    |
| HIPAA Security Rule      | US law for electronic protected health information                              | Access control, audit logs, encryption, integrity controls                        |
| GDPR (Article 32)        | EU law; "appropriate technical and organisational measures"                     | Encryption, access control, data residency, deletion on request                   |
| CIS Benchmarks           | Hardening guides per OS, cloud, and Kubernetes                                  | Node, cluster, and account configuration baselines                                |
| NIST CSF 2.0 / SP 800-53 | US framework and control catalogue; 800-53 underpins FedRAMP                    | Detailed control families, if you sell to US government                           |
| EU DORA                  | ICT resilience for financial entities; applies from 17 January 2025             | Incident reporting, resilience testing, third-party (cloud) risk                  |
| EU NIS2                  | Cyber security duties for essential and important entities                      | Risk management, incident reporting, supply chain security                        |
| EU Cyber Resilience Act  | Security duties for products with digital elements                              | Vulnerability handling, SBOMs; reporting duties apply from 11 September 2026      |

**The overlap is the most useful thing to know.** Encryption at rest, least-privilege access, reviewed changes, centralised tamper-resistant logs, vulnerability management, and backups appear in nearly every framework above, in different words. A platform that implements each of these once, as an automated control, and produces continuous evidence has satisfied most of the technical content of all of them. Running a separate programme per framework means building the same encryption control three times with three sets of screenshots. See [turning a framework into automated controls](./how-do-you-turn-a-compliance-framework-into-automated-platform-controls.md).

**What the platform owns, and what it does not.** The platform can make controls automatic for every team: encryption on by default, workload identity instead of static keys, GitOps so every change is a reviewed commit, audit logs shipped to an account operators cannot modify. It cannot satisfy training, background checks, vendor due diligence, physical security, or policy documents. Being precise about that boundary is more credible than claiming the platform "makes you compliant".

**Scope is a platform design decision.** PCI DSS applies to the cardholder data environment and everything connected to it. If card data can reach any cluster, every cluster is in scope. A platform that offers an isolated, separately governed environment for regulated workloads keeps the audit small for everyone else. This is one of the most practical ways a platform team saves the organisation money and time.

**Who benefits.** Application teams, most of all. On a good platform they inherit the technical controls by using the golden path, and the evidence is produced for them. The compliance and security teams get evidence as a query instead of a scramble before each audit. The trade-off is that the platform becomes part of the audit itself: its own changes, access, and policy set are sampled, so the platform team needs the same discipline it asks of others.

## Example

```text
One control, mapped once, reused across frameworks.

CONTROL  All production changes are reviewed and traceable
  SOC 2           CC8.1   change management
  ISO 27001:2022  A.8.32  change management
  PCI DSS v4.0.1  6.5     changes to system components are managed
  DORA            ICT change management in the risk management framework

  PLATFORM IMPLEMENTATION (applies to every team automatically)
    - branch protection: one approving review required on the deploy repository
    - GitOps: the cluster only runs what is in Git; manual changes are reverted
    - admission policy: only signed images built by the platform pipeline run

  EVIDENCE (produced continuously, not collected before the audit)
    - Git history: author, reviewer, timestamp, diff
    - pipeline records: build, tests, signature, provenance
    - GitOps sync history: what was applied, when, from which commit

  WHAT A TEAM HAS TO DO    use the golden path. Nothing else.
```

## Interview tips

- Name SOC 2 and ISO 27001 first as the near-universal pair, and say why: customers ask for them in procurement.
- Get the categories right: SOC 2 is an attestation report, ISO 27001 is a certifiable standard, PCI DSS is an industry standard, GDPR, HIPAA, DORA, and NIS2 are law. It is a quick, credible signal.
- Stress the overlap and "map once, evidence many times". That is the platform-shaped answer.
- Mention an EU regulation if relevant to the role. DORA (applying since January 2025) and the Cyber Resilience Act reporting duties (from 11 September 2026) are current and reach platform teams through incident reporting, third-party risk, and SBOMs.
- Explain that PCI scope is a platform design decision, and isolation keeps it small.
- Be explicit about what the platform cannot automate. It builds credibility with interviewers who have lived through an audit. For the evidence side, see [what audit trail a platform owes its auditors](./what-audit-trail-does-a-platform-owe-its-auditors.md).

---

[⬅ Back to Policy as Code and Governance](./README.md) · [All topics](../README.md)
