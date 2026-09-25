---
title: "How do you handle data residency and sovereignty requirements?"
id: 193
category: "Multi-Cloud and Hybrid Platforms"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - multi-cloud-and-hybrid-platforms
  - interview-questions
---

# How do you handle data residency and sovereignty requirements?

**Short answer:** First separate the three things people conflate: residency (where data is stored and processed), sovereignty (whose laws and whose people can reach it), and localisation (a legal rule that a copy must stay in-country). Then turn the requirement into platform controls: classify data, enforce allowed locations with organisation-level guardrails, control encryption keys, and follow the data everywhere it leaks - backups, logs, telemetry, support access, and AI services. Residency is mostly an engineering problem the platform can solve; sovereignty is partly legal and operational, and may push you to a sovereign cloud offering or on-premises.

## Detail

**Get the definitions right, because the controls differ.**

| Concept      | Question it answers                                 | Typical control                                          |
| ------------ | --------------------------------------------------- | -------------------------------------------------------- |
| Residency    | Where is the data stored and processed?             | Allowed-region guardrails, placement in the service spec |
| Localisation | Must a copy stay inside a specific country?         | In-country primary, restricted replication               |
| Sovereignty  | Which jurisdictions and which people can access it? | Key control, operator restrictions, sovereign offerings  |

A dataset can be fully resident in Frankfurt and still not meet a sovereignty requirement, because a provider headquartered elsewhere may be subject to foreign legal orders, and its global support staff may be able to access systems. That gap is why sovereignty questions end up with legal and procurement teams, not only engineers.

**Start from data classification, not from regions.** The platform cannot enforce a rule it cannot see. Each dataset and service gets a classification - for example `public`, `internal`, `personal-eu`, `regulated-health` - declared in the service specification and the catalogue. The classification maps to allowed locations, allowed replication targets, key requirements, and which managed services are permitted.

**Enforce locations with guardrails at the organisation level,** so a team cannot create a resource in the wrong place even by accident:

- **AWS**: a service control policy denying actions when `aws:RequestedRegion` is outside the allowed list (exempting global services), applied to the OU holding regulated accounts.
- **Azure**: the built-in "Allowed locations" policy assigned at the management group.
- **Google Cloud**: the `gcp.resourceLocations` organisation policy constraint, which accepts value groups such as `in:eu-locations`.

Guardrails stop resource creation; they do not stop data flowing out through an application. That needs the next layer.

**Follow the data everywhere it goes.** The primary database is rarely where residency fails. The leaks are secondary copies:

- Backups and snapshots replicated to a "DR region" outside the boundary.
- Logs and traces containing personal data shipped to a central observability backend in another region.
- Global services whose control or metadata plane runs elsewhere - some identity, CDN, and DNS services are global by design.
- Support cases where a customer's data is attached to a ticket handled worldwide.
- AI and analytics services that process prompts or data in a different region unless configured otherwise.

**Keys are the strongest technical sovereignty lever.** Customer-managed keys in a regional KMS keep the provider from decrypting data without your key. Going further, external key management - Google Cloud External Key Manager, AWS KMS External Key Store, or keys in a dedicated HSM you control - means the key never sits in the provider's key service, so access can be revoked by you. The trade-off is availability: if your external key service is down, so is every workload using it.

**Sovereign offerings shift some of the operational burden.** Providers now sell environments designed for sovereignty requirements: the AWS European Sovereign Cloud (generally available since January 2026, physically and logically separate from other AWS regions and operated by EU-resident staff), Microsoft's EU Data Boundary (completed in February 2025) plus its sovereign cloud offerings, and Google's sovereign options, including partner-operated clouds in some countries. These can close gaps that pure engineering cannot, but they often lag the main regions in available services, so check the service list against what your platform depends on. Where no offering fits, on-premises or a local provider becomes the answer - which makes the platform hybrid.

**Transfers are a legal mechanism, not a network one.** Moving personal data out of the EU relies on a legal basis such as an adequacy decision (the EU-US Data Privacy Framework for certified US companies) or standard contractual clauses with a transfer impact assessment. The platform's part is to make transfers visible and deliberate, so the privacy team can map them.

**Name the user.** Application teams should declare a classification and get a compliant placement automatically, with a clear validation error if they request a region or service the classification forbids. Compliance and privacy teams need evidence - a report of where each classified dataset lives, which keys protect it, and which flows cross a boundary. The platform provides both.

## Example

```yaml
# Service specification: the classification drives placement and validation.
apiVersion: platform.example.com/v1
kind: Service
metadata: { name: patient-records }
spec:
  owner: group:team-clinical
  dataClassification: regulated-health-eu
  placement: { provider: gcp, region: europe-west3 }
  dependencies:
    - postgres:
        size: large
        backups: { copies: 2, regions: [europe-west3, europe-west4] } # both in the EU
        encryption: { keyManagement: external } # key held outside the provider
  telemetry:
    logsBackend: eu-observability # EU-hosted; the global backend is refused
    redactFields: [patient_id, insurance_number, date_of_birth]
# Platform validation for this classification rejects:
#   - any backup or replica region outside the EU value group
#   - logs routed to a backend outside the EU
#   - managed services on the "not permitted for regulated-health" list
```

```yaml
# Organisation policy on the folder holding regulated projects:
# gcloud org-policies set-policy residency-policy.yaml
name: folders/123456789012/policies/gcp.resourceLocations
spec:
  rules:
    - values:
        allowedValues:
          - in:eu-locations
```

```text
Residency review for patient-records - the places data actually goes:

  primary database         europe-west3                         OK
  backups                  europe-west3, europe-west4           OK
  application logs         EU observability backend             OK, redacted fields
  traces                   sampled; attributes scrubbed         OK
  CDN edge cache           global                               NOT PERMITTED -> disabled
  support cases            provider EU support + access controls REVIEWED
  analytics export         none                                 OK
  encryption keys          external key manager, EU HSM         OK
```

## Interview tips

- Open by separating residency, localisation, and sovereignty. Many candidates use them interchangeably.
- Start from data classification in the service specification, then map it to organisation-level location guardrails in each cloud.
- The strongest content is "follow the data": backups, logs, telemetry, global services, support access, and AI services are where residency actually fails.
- Present external key management as the main technical sovereignty lever, and name its availability cost.
- Mention sovereign cloud offerings as a way to meet operational sovereignty requirements, with the caveat that service availability often lags the main regions. See [How does data gravity constrain platform design?](./how-does-data-gravity-constrain-platform-design.md) for why placement decisions are hard to reverse.

---

[⬅ Back to Multi-Cloud and Hybrid Platforms](./README.md) · [All topics](../README.md)
