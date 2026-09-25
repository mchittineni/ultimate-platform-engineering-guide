---
title: "How do you design multi-cloud disaster recovery without doubling cost?"
id: 197
category: "Multi-Cloud and Hybrid Platforms"
difficulty: "Advanced"
tags:
  - platform-engineering
  - multi-cloud-and-hybrid-platforms
  - interview-questions
---

# How do you design multi-cloud disaster recovery without doubling cost?

**Short answer:** Stop treating "the other cloud" as a mirror and start from the specific disasters you are protecting against. Most of them - a zone or region failure - are cheaper to handle within one provider, so the second cloud is reserved for the scenarios only it covers: losing the provider or the account itself, whether through a provider-wide failure, a compromised organisation, a contractual exit, or a regulator requiring it. For those, keep an immutable, independently controlled copy of the data in the second cloud, keep the infrastructure as code that can rebuild there, pre-arrange quotas and identity, and run warm standby only for the few services whose recovery time objective demands it. Then prove it with regular restores. The cost scales with data and rehearsal, not with a second running estate.

## Detail

**Decompose "disaster" into scenarios, and match each to the cheapest control.**

| Scenario                                     | Likelihood | Cheapest adequate control                                    |
| -------------------------------------------- | ---------- | ------------------------------------------------------------ |
| Zone failure                                 | Common     | Multi-zone within the region                                 |
| Region failure                               | Rare       | Multi-region within the same provider                        |
| Ransomware or destructive insider            | Plausible  | Immutable backups under separate credentials                 |
| Organisation or account compromise           | Plausible  | Backups in a separate trust domain - another cloud qualifies |
| Provider-wide control-plane outage           | Very rare  | Tier-0 recovery in a second provider                         |
| Forced exit (contract, sanctions, regulator) | Rare, slow | A tested ability to rebuild elsewhere within weeks           |

The cross-cloud rows are the ones where the attacker or failure has taken the whole provider trust domain. An independent copy of data in another cloud, under credentials that the compromised organisation cannot touch, is valuable against those - and it is the part of multi-cloud DR that is almost always worth its cost.

**Tier services by business impact and set RTO and RPO per tier.** A handful of services - payments, authentication, the thing the regulator asks about - may justify minutes of downtime and seconds of data loss. Most services can tolerate hours to a day. The platform's job is to make the tier a declared property, map each tier to a DR pattern, and refuse to let every team pick the most expensive one by default.

**The four patterns and their cost shape:**

- **Backup and restore.** Data copied to the second cloud; nothing running there. Cost is storage plus egress for the copy. Recovery is hours to days.
- **Pilot light.** Data replicated continuously; core infrastructure (network, identity, a small cluster, the database replica) exists but is scaled to minimum. Recovery is tens of minutes to hours.
- **Warm standby.** A scaled-down but functional copy of the service runs and receives replicated data. Recovery is minutes. Cost is a meaningful fraction of production.
- **Active-active.** Both sides serve traffic. Near-zero recovery time, but it requires cross-cloud data consistency and continuous egress, and it doubles much of the operational surface. Rarely justified across providers.

Putting only tier 0 on warm standby and everything else on backup and restore is how the bill stays well short of double.

**Data is the expensive and difficult part.** Compute can be rebuilt from images and code in minutes; data cannot. Use database-native, asynchronous replication or log shipping for tier 0, accepting a small RPO; use periodic logical backups for the rest. Keep backups immutable (S3 Object Lock, Azure immutable blob storage, Cloud Storage bucket lock) and write them from a pipeline whose credentials exist only for that purpose. Watch egress: the continuous copy is the main running cost, so compress, deduplicate, and copy deltas rather than full snapshots. From 12 January 2027 the EU Data Act removes egress charges for switching provider, but not for ongoing replication to a second cloud.

**Infrastructure as code is the standby.** A cold second cloud is only a recovery plan if the platform can be recreated there: landing zone, networking, identity federation, clusters, platform services, and application deployments, all from code. Keep the second-cloud modules in the same repository and run them in CI - a plan that is not exercised decays within months as the primary estate changes.

**Pre-arrange what cannot be created during a crisis.** Quotas and capacity (a new account's GPU or vCPU limits will not cover production), identity federation to the IdP, DNS delegation and certificates, container images mirrored to a registry in the second cloud, and secrets bootstrapped into a separate secret store. These are cheap to hold in advance and slow to obtain on the day.

**Protect the recovery path from the thing it recovers from.** If your IdP, CI system, Git host, or secrets manager runs only in the failed provider, you cannot rebuild. List the dependencies of the recovery procedure itself and make sure each is reachable without the primary cloud - including break-glass accounts in the second cloud.

**Rehearse, and measure against the objectives.** A restore test that has never run is a hypothesis. Run tier-0 failovers at least twice a year and restore a sample of lower-tier services every quarter, recording the actual recovery time and data loss against the target. In regulated sectors this is not optional: DORA requires financial entities to test ICT continuity and recovery plans and to have exit strategies for critical providers.

**Name the user.** Service owners declare their tier; the platform provides the pattern, the replication, the backups, and the runbook, and reports whether each service met its last test. Leadership and regulators get a single view: which services recover where, how fast, and when that was last proven.

## Example

```yaml
# Platform DR policy: tier drives pattern. Teams declare a tier, not a design.
drTiers:
  tier-0:
    services: [payments-api, auth, ledger]
    scenarios: [region, provider, account-compromise]
    pattern: warm-standby
    secondary: { provider: gcp, region: europe-west1 }
    rto: 30m
    rpo: 1m # async database replication
    test: { failover: semi-annual }
  tier-1:
    pattern: pilot-light-in-region # multi-region, same provider
    secondaryProviderCopy: backup-only
    rto: 4h
    rpo: 15m
    test: { restore: quarterly }
  tier-2:
    pattern: backup-restore
    secondaryProviderCopy: backup-only
    rto: 48h
    rpo: 24h
    test: { restore: sample-quarterly }
backups:
  immutability: { mode: compliance, retentionDays: 35 }
  writer: dedicated pipeline identity; no human or production role can delete
```

```yaml
# Kubernetes state for tier-2 services, backed up nightly from an EKS cluster to a
# Cloud Storage bucket in the second provider (velero-plugin-for-gcp installed).
apiVersion: velero.io/v1
kind: Schedule
metadata:
  name: nightly-tier2-to-gcp
  namespace: velero
spec:
  schedule: "0 2 * * *"
  template:
    includedNamespaces: [catalogue, search, notifications]
    storageLocation: gcp-dr-bucket
    snapshotMoveData: true # copy volume data to object storage, not provider snapshots
    ttl: 720h0m0s
```

```text
Why this is not double - where the spend goes, relative to production:

  tier-0 warm standby (3 services)      scaled to ~25% capacity    the main cost
  continuous replication egress         deltas, compressed         scales with change rate
  immutable backups in second cloud     storage only               grows with retention
  pre-arranged quotas, DNS, federation  near zero                  must be kept current
  cold platform (landing zone, clusters) created only in tests     CI plan runs weekly
  rehearsal                             engineer time              the non-negotiable part

Last tier-0 failover test (March): RTO target 30m, actual 41m.
  cause: container images for ledger not mirrored to the second registry
  fix: image mirroring moved into the release pipeline; retest in April -> 22m
```

## Interview tips

- Refuse the premise of a full mirror: decompose disasters into scenarios and show that most are cheaper to handle within one provider.
- Identify the scenarios only a second cloud covers - provider-wide failure, organisation compromise, forced exit - and argue that an immutable, independently controlled data copy is the high-value part.
- Tier services, set RTO and RPO per tier, and map tiers to backup-restore, pilot light, warm standby, or active-active, with active-active across providers rarely justified.
- Stress the hidden dependencies: quotas, identity, DNS, images, and a recovery path that does not depend on the failed provider.
- Close on rehearsal with measured results, and mention DORA's testing and exit-strategy requirements for financial services. See [How do you plan disaster recovery for the platform itself?](../platform-reliability/how-do-you-plan-disaster-recovery-for-the-platform-itself.md) for the platform's own control plane.

---

[⬅ Back to Multi-Cloud and Hybrid Platforms](./README.md) · [All topics](../README.md)
