---
title: "What are RTO and RPO, and how do they differ from high availability?"
id: 201
category: "Platform Reliability"
difficulty: "Beginner"
tags:
  - platform-engineering
  - platform-reliability
  - interview-questions
---

# What are RTO and RPO, and how do they differ from high availability?

**Short answer:** The recovery time objective (RTO) is how long a service may be down after a disaster before the business is seriously harmed; the recovery point objective (RPO) is how much data, measured in time, you can afford to lose. Both are targets for disaster recovery - recovering from losing a whole region, account, or dataset. High availability is a different thing: designing a service so that ordinary failures, such as a node, instance, or zone dying, are absorbed automatically with little or no downtime. You need both, because high availability faithfully replicates the mistakes that disaster recovery exists to undo.

## Detail

**RTO is about time to restore service.** An RTO of one hour means that, from the moment of the disaster, the service must be usable again within an hour. It covers everything: noticing the problem, deciding to fail over, running the procedure, and checking it worked. Teams routinely underestimate the first two.

**RPO is about data you can lose.** An RPO of 15 minutes means that after recovery, at most the last 15 minutes of writes may be missing. It is determined by how often data leaves the failing location: nightly backups give an RPO of up to 24 hours, continuous log shipping gives minutes, and synchronous replication gives close to zero. RPO is a data question, so a stateless service has none - only its datastores do.

**Tighter objectives cost more, non-linearly.** Going from "restore from last night's backup within a day" to "fail over to another region within five minutes with no data loss" means running a second environment continuously, replicating data across regions, and accepting the latency cost of synchronous writes. Cloud providers describe a ladder of strategies - backup and restore, pilot light, warm standby, and multi-site active-active - each cheaper to run but slower to recover than the next. The objectives should come from the business impact of the service being down, not from ambition.

**High availability handles expected failures automatically.** Running three replicas across three availability zones behind a load balancer, or a database with a synchronous standby in another zone, means a failed instance or zone causes seconds of disruption and no human action. HA is measured by the availability SLO, and it is continuously exercised by normal failures.

**Why HA is not DR.** Replication copies everything, including the bad things. If someone runs `DROP TABLE`, a faulty migration corrupts rows, or ransomware encrypts a volume, every replica receives the damage within milliseconds. Likewise, HA inside one region does nothing if the region, the cloud account, or the credentials are lost. Disaster recovery needs copies that are separate in time (point-in-time backups), in place (another region), and in control (another account, ideally immutable), so the thing that destroyed production cannot also destroy the backup.

**A backup you have not restored is a hope.** The only way to know your real RTO and RPO is to restore on a schedule and time it. Restores regularly reveal missing permissions, undocumented steps, or backups that were silently failing. In regulated sectors this is no longer optional: the EU's Digital Operational Resilience Act (DORA), which applies to financial entities from 17 January 2025, requires backup and recovery arrangements and regular testing of ICT business continuity and recovery plans.

**For a platform team, set objectives per capability.** The users are engineering teams, and their needs differ by capability: traffic serving must recover in minutes, the ability to deploy can tolerate hours, and the developer portal can wait a day. The platform also provides DR as a capability - backup policies, cross-region copies, and restore tooling that teams opt into by tier rather than each building their own. The [platform DR question](./how-do-you-plan-disaster-recovery-for-the-platform-itself.md) covers recovering the platform itself.

## Example

```text
One service, two different problems - and which mechanism covers each.

  FAILURE                       COVERED BY   RTO        RPO       MECHANISM
  one pod or node dies          HA           seconds    0         3 replicas, 3 zones
  one availability zone fails   HA           < 1 min    0         sync standby DB in
                                                                  another zone
  bad migration corrupts rows   DR           2h         5 min     point-in-time restore
                                                                  from WAL archive
  region unavailable            DR           1h         15 min    async cross-region
                                                                  replica, promoted
  account compromised or        DR           8h         24h       daily immutable backup
  ransomware                                                      in a separate account

  HA would have copied the corrupted rows to the standby within milliseconds.
  Only a copy separated in time, place, and control helps with the last three.
```

```yaml
# Velero backing up platform control-plane state hourly to a bucket in
# another region: this schedule is what sets an RPO of one hour for it.
apiVersion: velero.io/v1
kind: Schedule
metadata:
  name: platform-control-plane-hourly
  namespace: velero
spec:
  schedule: "0 * * * *" # hourly -> RPO of at most 1h for these resources
  template:
    includedNamespaces:
      - argocd
      - crossplane-system
    storageLocation: dr-eu-west-2 # a BackupStorageLocation in another region
    snapshotVolumes: false
    ttl: 720h0m0s # 30 days of restore points
```

## Interview tips

- Define both in one line each: RTO is how long you can be down, RPO is how much data you can lose. Then say they are disaster recovery targets.
- The key distinction is the one about replication: HA copies corruption and deletions instantly, so it cannot replace backups separated in time, place, and control.
- Tie RPO to a mechanism - backup frequency, log shipping, or synchronous replication - to show you know where the number comes from.
- Say that tighter objectives cost non-linearly, and that the business impact should set them. Naming the backup-and-restore to active-active ladder helps.
- "An untested backup is a hope" is the practical close; mention timed restore rehearsals and, for financial services, DORA's testing requirements.
- Name the user: for a platform team, objectives differ per capability, and backups and restores should be something teams opt into by tier.

---

[⬅ Back to Platform Reliability](./README.md) · [All topics](../README.md)
