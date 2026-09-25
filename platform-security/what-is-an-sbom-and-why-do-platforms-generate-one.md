---
title: "What is an SBOM and why do platforms generate one?"
id: 120
category: "Platform Security"
difficulty: "Beginner"
tags:
  - platform-engineering
  - platform-security
  - interview-questions
---

# What is an SBOM and why do platforms generate one?

**Short answer:** A software bill of materials (SBOM) is a machine-readable list of every component inside a piece of software - libraries, their versions, where they came from, and their licences - including the transitive dependencies nobody chose directly. Platforms generate one automatically for every build, attach it to the artefact, and index it, so that when a new vulnerability is published the question "where are we running this?" takes minutes instead of days. Regulation is now adding a second reason: the EU Cyber Resilience Act requires manufacturers to maintain one.

## Detail

**What is in it.** An SBOM is an inventory, the software equivalent of the ingredients label on food. For each component it records a name, a version, and ideally a universal identifier - a Package URL (purl) such as `pkg:maven/org.apache.logging.log4j/log4j-core@2.17.1` - so tools can match it against vulnerability databases without guessing. Good SBOMs also record the dependency relationships (what pulled this in), hashes, and licences.

**The two formats you will meet:**

| Format    | Origin                                | Strength                                          |
| --------- | ------------------------------------- | ------------------------------------------------- |
| SPDX      | Linux Foundation; ISO/IEC 5962 (v2.2) | Licence compliance heritage; 3.0 adds profiles    |
| CycloneDX | OWASP; Ecma standard ECMA-424         | Security focus; also covers services, crypto, VEX |

Both are fine and most tools emit and read both. The current specifications are SPDX 3.0.1 and CycloneDX 1.7, but plenty of tooling still produces SPDX 2.3 or CycloneDX 1.5/1.6 - pick one format as the platform's standard and make sure your consumers (scanners, the index, any customers you must hand SBOMs to) accept the version you produce.

**Why a platform generates it rather than each team.** If SBOMs depend on every team adding a step to their pipeline, coverage will be partial, and a partial inventory is dangerous because it looks complete. When the platform's build templates generate the SBOM for every image, coverage is a property of the build path. Application teams get it for free and never think about it.

**The value is in the query, not the file.** An SBOM sitting in a build artefact is not useful by itself. The platform's job is to collect every SBOM into an index linked to what is actually deployed, so it can answer:

- Which running services contain this library at a vulnerable version?
- Which of those are internet-facing, and who owns them?
- Which images have no SBOM at all? (the blind spots)

That capability is what turns a critical advisory from a multi-day hunt across forty teams into a list you have within minutes. It must exist before the day you need it.

**Where SBOMs come from, and why that matters.** They can be generated from source (reading lockfiles) or from the built image (scanning what was actually installed). Image scanning catches things lockfiles miss - OS packages from the base image, binaries copied in - while source analysis sees dependency relationships more clearly. Many platforms generate from the image because that is what runs.

**Limitations to be honest about.** An SBOM is only as accurate as the tool that produced it. Statically linked binaries, vendored code, and components downloaded at runtime are often missed. An SBOM also tells you a component is _present_, not that its vulnerable code is _reachable_ - which is why it is paired with VEX (Vulnerability Exploitability eXchange) statements that record "we contain this, but it is not exploitable here, and here is why". And an SBOM from a vendor is a claim; you still want to generate your own for third-party images you run.

**Sign it.** An SBOM attached as a signed attestation to the image digest cannot be swapped out afterwards, so consumers can trust that it describes that exact artefact.

## Example

```bash
# In the platform's build template, after the image is pushed by digest.
# syft generates the SBOM from the built image, not just the lockfile.
IMAGE="ghcr.io/example/checkout@${DIGEST}"
syft "$IMAGE" -o cyclonedx-json=sbom.cdx.json

# Attach it to the image as a signed attestation (keyless, CI identity).
cosign attest --yes --type cyclonedx --predicate sbom.cdx.json "$IMAGE"

# Scan the SBOM rather than re-scanning the image - fast, and repeatable
# later against new advisories without rebuilding anything.
grype sbom:./sbom.cdx.json --only-fixed --fail-on critical
```

```json
{
  "bomFormat": "CycloneDX",
  "specVersion": "1.6",
  "metadata": {
    "component": { "type": "container", "name": "ghcr.io/example/checkout" }
  },
  "components": [
    {
      "type": "library",
      "name": "log4j-core",
      "version": "2.17.1",
      "purl": "pkg:maven/org.apache.logging.log4j/log4j-core@2.17.1"
    },
    {
      "type": "library",
      "name": "openssl",
      "version": "3.0.15-1~deb12u1",
      "purl": "pkg:deb/debian/openssl@3.0.15-1~deb12u1?distro=debian-12"
    }
  ]
}
```

```text
What the index buys you on the day an advisory lands:

  $ platform sbom query --package log4j-core --version "<2.17.1"

  running services affected ........ 3
    team-search/indexer    2.16.0   internet-facing   owner: team-search
    team-data/etl-runner   2.14.1   internal          owner: team-data
    team-data/sync         2.14.1   internal          owner: team-data
  running images with no SBOM ...... 1   <-- vendor image, treat as affected
```

## Interview tips

- Define it simply - an ingredients list for software, including transitive dependencies - then move quickly to why: answering "where are we affected?" fast.
- Name the user: application teams get SBOMs without doing anything, and the security and platform teams get an estate-wide inventory. Coverage comes from the build path, not from discipline.
- Stress that the value is in the index linked to what is deployed, not in the file itself. That distinction separates a strong answer from a checkbox one.
- Know the two formats (SPDX, CycloneDX) and that the choice matters less than consistency and consumer support.
- Mention the limitations - missed components, presence versus reachability - and VEX as the way to record "present but not exploitable".
- Regulation is a good follow-up: the [EU Cyber Resilience Act](./what-does-the-eu-cyber-resilience-act-mean-for-a-platform-team.md) requires manufacturers to draw up an SBOM. For the incident side, see [responding to a fleet-wide CVE](./how-do-you-respond-to-a-critical-cve-that-affects-every-service-on-the-platform.md).

---

[⬅ Back to Platform Security](./README.md) · [All topics](../README.md)
