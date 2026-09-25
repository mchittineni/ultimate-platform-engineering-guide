---
title: "What does the EU Cyber Resilience Act mean for a platform team?"
id: 126
category: "Platform Security"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - platform-security
  - interview-questions
---

# What does the EU Cyber Resilience Act mean for a platform team?

**Short answer:** The Cyber Resilience Act (Regulation (EU) 2024/2847) makes manufacturers of "products with digital elements" sold in the EU legally responsible for their security across a declared support period. Its vulnerability and incident reporting duties have applied since 11 September 2026 - an actively exploited vulnerability must be flagged to the national CSIRT and ENISA within 24 hours - and the full essential requirements, including an SBOM and CE marking, apply from 11 December 2027. For a platform team, the Act turns things that used to be good practice - SBOMs, provenance, vulnerability intake, fleet-wide inventory - into evidence the company must be able to produce on a deadline, and the platform is where that evidence is generated.

## Detail

**Scope first, because it decides everything.** The CRA covers hardware and software products placed on the EU market in the course of a commercial activity: installable software, firmware, devices, desktop and mobile apps, libraries sold or monetised, and the "remote data processing solutions" a product needs to work (a device's cloud back end, for example). Pure software as a service is generally outside it (the provider may instead be in scope of NIS2 as an entity), and so are internal tools never placed on the market. So the first question for a platform team is not "what do we run?" but "which of the things we build does the company ship to customers?" A company that only runs a web application may have limited exposure; one that ships an agent, an SDK, an on-premises edition, or a connected device is squarely in scope.

**The dates that matter:**

| Date              | What applies                                                                      |
| ----------------- | --------------------------------------------------------------------------------- |
| 10 December 2024  | Entry into force                                                                  |
| 11 June 2026      | Rules for notifying conformity assessment bodies apply                            |
| 11 September 2026 | Reporting of actively exploited vulnerabilities and severe incidents (Article 14) |
| 11 December 2027  | All remaining obligations: essential requirements, conformity, CE marking         |

Crucially, the Article 14 reporting duty applies to products already on the market, not just new ones. Products placed on the market before 11 December 2027 only have to meet the essential requirements if they are substantially modified after that date - but reporting applies to all of them now.

**The reporting clock.** On becoming aware of an actively exploited vulnerability in its product, the manufacturer must send, through ENISA's Single Reporting Platform to the CSIRT of its main establishment (with ENISA notified simultaneously):

- an **early warning within 24 hours**,
- a **vulnerability notification within 72 hours** with more detail and any mitigations,
- a **final report within 14 days** of a corrective or mitigating measure being available.

Severe incidents affecting the product's security follow the same 24- and 72-hour steps, with a final report within a month. The manufacturer must also inform affected users and, where needed, tell them how to mitigate. Twenty-four hours is not long enough to discover _whether_ you are affected by asking teams, so the ability to answer "which shipped versions of which products contain this component, and is it being exploited?" has become a compliance capability.

**What the essential requirements ask for (from December 2027).** Annex I sets them out, with Article 13 adding the manufacturer duties. The ones that land on a platform:

- **Secure by default** delivery, no known exploitable vulnerabilities at release, and minimised attack surface.
- **An SBOM** in a commonly used, machine-readable format covering at least the top-level dependencies, kept as part of the technical documentation. It does not have to be published, but must be available to market surveillance authorities.
- **Vulnerability handling** throughout the support period: a coordinated disclosure policy, a contact address for reports, security updates delivered without delay and free of charge, and separated from feature updates where technically feasible.
- **A support period** of at least five years unless the product's expected use is shorter, with the end date stated at purchase. Each security update must stay available for at least ten years after issue or for the rest of the support period, if longer.
- **Due diligence on third-party components**, including open source you integrate - you are responsible for the whole product, not just your own code.

Most products can self-assess conformity. Products listed as "important" (class I or II) or "critical" need harmonised standards, a certification scheme, or a third-party assessment. Penalties for breaching the essential requirements reach €15 million or 2.5% of worldwide annual turnover, whichever is higher.

**Where the platform comes in.** The obligations sit with the company as manufacturer, but nearly all the evidence is produced by the build and release path:

- **SBOM per released version, retained.** Not just per deployed image - per _shipped_ artefact, kept for as long as the documentation must be kept (ten years after placing on the market or the end of the support period, whichever is longer). The index must be able to answer for versions customers still run, not only what is in production today.
- **Provenance and signing** for release artefacts, so you can show what was built from what.
- **Vulnerability intake to decision in hours.** Feeds for new advisories, exploitation signals such as CISA's Known Exploited Vulnerabilities catalogue, and a matching step against the release SBOM index, with an on-call owner who can decide whether the 24-hour clock has started.
- **VEX statements** to record "present but not exploitable", which cuts the number of candidate notifications and documents the reasoning.
- **Release metadata** that ties each product version to its support end date, so the platform knows which versions still need security updates.

**Trade-offs and honest limits.** The Act is new and some of it is still being made concrete through harmonised standards and Commission guidance, so specific interpretations belong with legal and compliance colleagues, not the platform team. Over-scoping is a real cost: treating internal-only tooling as a CRA product adds process without legal benefit. Under-scoping is worse. The platform team's job is to make the capability cheap enough that scope decisions are about the law, not about whether the tooling exists.

## Example

```yaml
# Release record the platform writes for every shipped version. It is the join
# key between an advisory, the SBOM index, and the support obligations.
apiVersion: releases.platform.example.com/v1
kind: ProductRelease
metadata:
  name: edge-agent-4.12.0
spec:
  product: edge-agent # installable agent shipped to customers - in CRA scope
  version: 4.12.0
  releasedAt: "2026-09-02"
  supportEndsAt: "2031-09-30" # declared at purchase; >= 5 years
  artefacts:
    - ref: ghcr.io/example/edge-agent@sha256:3c9e...a1
      sbom: sbom/edge-agent-4.12.0.cdx.json # CycloneDX, signed attestation
      provenance: slsa-provenance-v1 # attested by the release workflow
  retention:
    technicalDocumentationUntil: "2036-09-02" # 10 years from placing on the market, or the support period if longer
```

```text
A 24-hour clock, run from the platform's tooling:

  T+0h00  KEV feed adds CVE in libexample (actively exploited).
  T+0h05  $ platform sbom query --package libexample --version "<2.8.4" --scope shipped

            SHIPPED, IN SUPPORT
              edge-agent 4.10.x - 4.12.0     via direct dependency
              desktop-client 7.3.x           via transitive (image-lib)
            SHIPPED, OUT OF SUPPORT
              edge-agent 3.x                 support ended 2026-03 -> no update duty,
                                             reporting still assessed with legal
            RUNNING ONLY (SaaS back end)     handled under the incident process

  T+0h40  Exploitability: desktop-client never calls the vulnerable parser -> VEX
          "not_affected: vulnerable_code_not_in_execute_path", reviewed and signed.
          edge-agent exposes it on a local port -> affected.
  T+2h00  Product security confirms awareness; early warning submitted via the
          Single Reporting Platform (edge-agent only).
  T+20h   Patched edge-agent 4.12.1 built, signed, SBOM attested.
  T+48h   72-hour notification with fix and mitigation; users informed.
  T+14d   Final report after corrective measure available.

  Without a release-scoped SBOM index, step T+0h05 is the part that takes days.
```

## Interview tips

- Start with scope: products with digital elements placed on the EU market. Say explicitly that pure SaaS is largely outside it and internal tools are too, so the first job is identifying what the company actually ships.
- Get the dates right - in force December 2024, reporting from 11 September 2026, full application 11 December 2027 - and mention that reporting applies to products already on the market.
- Know the 24-hour / 72-hour / 14-day sequence and that it is triggered by an _actively exploited_ vulnerability, not every CVE.
- Name the user: product and security teams need the platform to answer "which shipped versions contain this?" in minutes. Stress _shipped versions under support_, not just what is running.
- Tie it to existing supply-chain work: SBOM, provenance, signing, and VEX become evidence rather than nice-to-haves. See [what an SBOM is](./what-is-an-sbom-and-why-do-platforms-generate-one.md), [supply-chain security](./how-do-you-secure-the-software-supply-chain-for-everything-the-platform-builds.md), and [turning compliance frameworks into controls](../policy-as-code-and-governance/how-do-you-turn-a-compliance-framework-into-automated-platform-controls.md).
- Be clear that legal interpretation belongs with counsel. Interviewers value a candidate who knows the mechanism and knows where their remit ends.

---

[⬅ Back to Platform Security](./README.md) · [All topics](../README.md)
