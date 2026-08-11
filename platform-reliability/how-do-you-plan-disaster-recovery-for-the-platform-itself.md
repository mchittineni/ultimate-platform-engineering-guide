---
title: "How do you plan disaster recovery for the platform itself?"
id: 109
category: "Platform Reliability"
difficulty: "Advanced"
tags:
  - platform-engineering
  - platform-reliability
  - interview-questions
---

# How do you plan disaster recovery for the platform itself?

**Short answer:** Make the platform reproducible from version control so recovery is rebuilding rather than restoring, identify the small amount of state that genuinely cannot be rebuilt and protect that properly, and rehearse the rebuild on a schedule with a timed result. The two things that will actually hurt are control-plane state that records what you provisioned - losing it means orphaned or duplicated infrastructure - and a recovery procedure that depends on the platform you are recovering.

## Detail

**Most of a platform should be rebuildable, not recoverable.** If clusters, components, policies, and configuration are all declared in Git and reconciled, then recovering a cluster is creating a new one and pointing the reconciler at the repository. That is a far better position than restoring backups, because it is exercised continuously by normal operation rather than only in a disaster.

**Identify what is genuinely irreplaceable, because that list is short and important:**

| State                                               | Rebuildable?  | Consequence of loss                                  |
| --------------------------------------------------- | ------------- | ---------------------------------------------------- |
| Cluster and component definitions                   | Yes, from Git | None beyond time                                     |
| Policies, RBAC, tenant definitions                  | Yes, from Git | None beyond time                                     |
| Control-plane records of provisioned infrastructure | **No**        | Orphaned or duplicated real resources                |
| Tenant application data                             | No            | Data loss - the worst case                           |
| Secrets and their versions                          | No            | Cannot restore access without rotation               |
| Container images and artefacts                      | Partly        | Rebuildable if sources exist; provenance may be lost |
| Audit logs                                          | No            | Compliance and forensic gap                          |
| Certificate authorities and signing keys            | No            | Trust chain broken across the estate                 |

**The third row is the platform-specific hazard.** If your control plane knows it created a database and you lose that record, the database still exists and nothing manages it - or worse, a rebuilt control plane creates a second one. This is why control-plane state gets backup rigour normally reserved for production data, and why resource-level tagging matters: tags let you reconcile reality against a rebuilt control plane and find the orphans.

**Back up etcd or the equivalent, and test restoring it.** For a self-managed control plane this is your responsibility; for a managed one, understand precisely what the provider guarantees. Either way, the custom resources describing tenants, claims, and platform configuration live there and a restore is what recovers the mapping between declarations and real infrastructure.

**Protect signing keys and certificate authorities as the highest tier.** If the authority that issues workload certificates is lost, every workload's identity is broken simultaneously. If image signing material is lost, you cannot verify or produce trusted artefacts. These are small, high-consequence items and they deserve treatment closer to a root credential than to configuration.

**The recovery procedure must not depend on the platform.** If rebuilding requires the pipeline, the registry, the secret store, or the identity integration - and those live on the platform - you have a circular dependency. The bootstrap path should be minimal, documented, externally hosted, and tested: a small script or pipeline that can create a cluster, install the reconciler, and let everything else follow.

**Set targets per capability, not one for the platform.** Restoring the ability to serve traffic is urgent; restoring the ability to deploy is important but tolerable for longer; restoring the portal is not urgent at all. Stating recovery objectives per capability is what makes the plan proportionate and affordable.

**Rehearse, and time it.** Rebuild a cluster from Git in a scratch account on a schedule, and record how long it takes and what needed manual intervention. Every rehearsal finds something - a bootstrap secret nobody documented, a component whose installation order matters, a hard-coded reference to the old cluster's name. A plan that has never been executed is a document, not a capability.

## Example

```text
Recovery objectives per capability - proportionate, and therefore affordable.

  CAPABILITY                   RTO      RPO      MECHANISM
  ingress / traffic serving    5m       n/a      multi-cluster; DNS failover to
                                                 the partner cluster
  tenant application data      1h       5m       managed backups + PITR per
                                                 datastore, per tier
  deploy capability            4h       0        rebuild cluster from Git; the
                                                 repo IS the backup
  provisioning capability      4h       15m      rebuild + restore control-plane
                                                 state (etcd) to recover the
                                                 record of what exists
  secret delivery              1h       0        managed store is regional and
                                                 replicated; rebuild the driver
  observability                8h       1h       rebuild; accept a telemetry gap
  portal / catalogue           48h      24h      lowest priority; regenerated
                                                 from repo descriptors

  Note the different RPOs. Deploy has RPO 0 because Git is the source of truth.
  Provisioning has RPO 15m because losing the control-plane record is the thing
  that causes orphaned infrastructure.
```

```text
Rebuild rehearsal, timed - and the findings, which are the point.

  $ platform dr rehearse --target scratch-account --from-scratch

  [1/9]  bootstrap: create cluster (Terraform, external pipeline)      11m 20s
         -> the bootstrap pipeline runs OUTSIDE the platform. Verified: it needs
            only the cloud credential and the Terraform state, both external.
  [2/9]  install GitOps reconciler (bootstrap script)                   1m 40s
  [3/9]  register cluster in the fleet definition                       0m 30s
  [4/9]  platform bundle reconciles (9 components)                      8m 10s
  [5/9]  policies, RBAC, tenant definitions applied                     2m 05s
  [6/9]  restore control-plane state (custom resources)                 4m 30s
         -> this is what recovers the MAPPING between claims and real
            infrastructure. Without it, step 7 would create duplicates.
  [7/9]  reconcile against reality: 218 claims vs actual cloud resources 6m 15s
         orphans found ........ 3   (resources with no claim - from a previous
                                     partial rebuild; adopted, not recreated)
         duplicates avoided ... 0   (because step 6 succeeded)
  [8/9]  tenant workloads reconcile                                    14m 50s
  [9/9]  verification: SLO probes green across capabilities             3m 05s
  ------------------------------------------------------------------------------
  TOTAL                                                                52m 45s
  (RTO target for deploy capability: 4h. Comfortable.)

  FINDINGS - every rehearsal produces some
    ✗ the observability collector's config referenced the OLD cluster name;
      hard-coded, not templated. Fixed.
    ✗ one bootstrap secret (the registry pull credential) was not documented
      anywhere - a team member happened to know it. Now in the sealed
      break-glass store with a retrieval procedure.
    ⚠ component install order matters between the CNI and the policy webhook;
      not previously recorded. Now encoded as a sync wave.
    ✓ no manual steps other than the two findings above.
```

```text
The irreplaceable list, and how each is protected:

  control-plane state (etcd / custom resources)
    hourly snapshot -> separate account, immutable storage, 30d retention
    restore tested monthly as part of the rehearsal
    resource TAGGING is the safety net: lets a rebuilt control plane reconcile
    against reality and find orphans rather than creating duplicates

  certificate authority + image signing material
    highest tier. Offline copy, split custody, restore drilled annually.
    losing this breaks every workload's identity simultaneously - it is closer
    to a root credential than to configuration.

  secrets
    managed store with its own replication; versions retained.
    recovery assumption: if the store is genuinely lost, rotation is the path,
    not restoration - so the rotation procedure must work at scale. Drilled.

  audit logs
    written to a separate account the audited systems cannot modify.
    retention 13 months. Loss is a compliance gap, so it is protected
    independently of everything else.
```

## Interview tips

- Lead with "rebuild, not restore", and explain why it is a better position: the rebuild path is exercised by normal operation, whereas a restore path is only exercised in a disaster.
- The control-plane state hazard is the platform-specific answer and the one interviewers are listening for: losing the record of what you provisioned means orphaned or duplicated real infrastructure.
- Resource tagging as the safety net that lets a rebuilt control plane reconcile against reality is a concrete, clever detail.
- Certificate authorities and signing keys as the highest tier, because losing them breaks every workload's identity at once, is a distinctive point.
- The circular dependency in the recovery path - needing the pipeline, registry, or identity that live on the platform - and a minimal externally hosted bootstrap is essential.
- Per-capability recovery objectives make the plan proportionate; one platform-wide RTO either over-invests or under-invests.
- Close on timed rehearsals and the findings they produce. The undocumented bootstrap secret that one person happened to know is the most realistic finding you can name.

---

[⬅ Back to Platform Reliability](./README.md) · [All topics](../README.md)
