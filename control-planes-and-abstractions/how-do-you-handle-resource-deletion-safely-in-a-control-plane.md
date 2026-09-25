---
title: "How do you handle resource deletion safely in a control plane?"
id: 77
category: "Control Planes and Abstractions"
difficulty: "Advanced"
tags:
  - platform-engineering
  - control-planes-and-abstractions
  - interview-questions
---

# How do you handle resource deletion safely in a control plane?

**Short answer:** Make deletion of anything holding data require an explicit, separate act - orphan the underlying resource by default rather than destroying it, block deletion at admission unless an approval annotation is present, and never let an indirect action such as deleting a namespace or a Git directory cascade into destroying a database. The core insight is that a reconciling control plane makes deletion as easy as creation, and those two operations do not deserve equal ease.

## Detail

**Why this is sharper in a control plane than in a script.** When infrastructure is represented as declarative objects, removing the object means removing the infrastructure - and objects get removed in ways nobody intends: a deleted namespace, a pruned Git directory, an accidental `kubectl delete -f` against the wrong file, a label selector change that makes a GitOps tool think a resource is no longer wanted. Each of these is a normal, low-ceremony action that can destroy production data.

**The asymmetry principle.** Creating a database should take seconds and no approval. Destroying one should require an explicit statement of intent that cannot be produced accidentally. Any design where the same gesture does both, differing only by direction, is unsafe regardless of how careful the team is.

**The layered defences, and you want several because each one has a bypass:**

- **Deletion policy on the managed resource.** Set it to orphan for anything stateful, so removing the control-plane object leaves the real resource in place, tagged as orphaned. You can always clean up deliberately later; you cannot un-drop a database. In Crossplane v2 the namespaced managed resources no longer have a `deletionPolicy` field - the equivalent is `managementPolicies` that omit `Delete` (for example `["Create", "Observe", "Update", "LateInitialize"]`), which the composition should set for every stateful resource.
- **Admission policy on delete.** Reject deletion of production stateful claims unless a specific annotation is present. The annotation is the explicit act - it cannot be produced by a namespace deletion or a Git prune.
- **Cloud-side protection.** Deletion protection on the database, object lock or versioning on buckets, `prevent_destroy` on Terraform resources. This is the backstop for when your control plane is the thing that is wrong.
- **Turn off automatic pruning for stateful resources.** GitOps pruning is correct for Deployments and dangerous for databases. Scope it by resource type, or exclude stateful claims from prune entirely.
- **Finalizers to sequence cleanup**, so credentials are revoked and snapshots taken before anything is released - and with an escape route, because a stuck finalizer blocks namespace deletion indefinitely.

**Retention on the way out.** When a deletion is genuinely intended, take a final snapshot and record where it is and when it expires. "Deleted with a 30-day recoverable snapshot" is a far better default than "deleted", and it converts a catastrophic mistake into an inconvenient one.

**Make the dangerous case loud.** A plan or diff that deletes a stateful resource should be visually distinct and require a different approval from ordinary changes. Most destructive incidents are not caused by someone deciding to destroy a database; they are caused by a destroy line inside a large diff that nobody read closely.

**Test the recovery path, not just the protection.** The valuable exercise is deliberately deleting a claim in a staging environment and confirming the resource survives, then deliberately destroying one and confirming the snapshot restores. Protections configured and never exercised have a habit of not working.

## Example

```yaml
# Layer 1 - orphan by default for anything stateful. Deleting the claim removes
# the control-plane object and leaves the database, tagged for later cleanup.
apiVersion: platform.example.com/v1
kind: PostgresInstance
metadata:
  name: checkout-db
  namespace: team-payments
  annotations:
    # GitOps must not prune this even if the directory disappears
    argocd.argoproj.io/sync-options: Prune=false
spec:
  size: small
  pitr: true
  deletionPolicy: Orphan # NOT Delete, for anything holding data - the composition
  # maps this to managementPolicies without "Delete" on the managed resource
  providerConfig:
    deletionProtection: true # Layer 3 - cloud-side backstop
    finalSnapshot: true
    finalSnapshotRetentionDays: 30
```

```yaml
# Layer 2 - admission policy. The annotation is the explicit act of intent, and
# it cannot be produced by a namespace deletion or a Git prune.
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicy
metadata: { name: protect-stateful-deletion }
spec:
  failurePolicy: Fail
  matchConstraints:
    resourceRules:
      - apiGroups: ["platform.example.com"]
        apiVersions: ["v1"]
        operations: ["DELETE"]
        resources: ["postgresinstances", "buckets", "queues"]
  matchConditions:
    - name: production-only
      expression: "oldObject.metadata.labels['platform.example.com/environment'] == 'production'"
  validations:
    - expression: >
        has(oldObject.metadata.annotations) &&
        'platform.example.com/approve-destroy' in oldObject.metadata.annotations &&
        oldObject.metadata.annotations['platform.example.com/approve-destroy'] == oldObject.metadata.name
      message: >
        Deleting a production stateful resource requires the annotation
        platform.example.com/approve-destroy set to the resource's own name.
        Run: platform destroy postgresinstance <name> --confirm <name>
      reason: Forbidden
```

```text
The four accidental paths, and which layer stops each one:

  1. `kubectl delete namespace team-payments`
       -> admission policy rejects the child claim deletion (Layer 2)
       -> even if bypassed, deletionPolicy: Orphan preserves the database (Layer 1)

  2. Someone deletes the Git directory; GitOps prunes
       -> Prune=false on the claim; the reconciler reports it as out of sync
          rather than deleting it (Layer 4)

  3. Terraform plan proposes replacing the database (a forces-new-resource change)
       -> prevent_destroy lifecycle rule fails the plan (Layer 3)
       -> CI check blocks any plan destroying aws_db_instance without a label

  4. The control plane itself is wrong - a bad composition removes the resource
       -> cloud-side deletionProtection refuses (Layer 3)
       -> final snapshot exists if all else fails

  No single layer covers all four, which is the argument for having all of them.

Quarterly verification - protections that are never exercised tend not to work:
  $ platform drill deletion-safety --env staging
    ✓ deleting a claim orphaned the RDS instance (not destroyed)
    ✓ namespace deletion blocked by admission policy
    ✓ GitOps prune did not remove the claim
    ✓ final snapshot restored to a scratch instance; row counts matched
```

## Interview tips

- The asymmetry principle is the thesis: creation should be trivial, destruction should require an explicit act that cannot be produced accidentally.
- Name the accidental paths - namespace deletion, Git prune, a label change - because they are what actually causes these incidents, not deliberate destroys.
- "Orphan, do not delete, for anything stateful" is the single most useful concrete default, and it is easy to state and defend.
- Layered defences with the observation that each layer has a bypass is what makes the answer sound like it came from an incident review rather than a document.
- Close on drilling the recovery path in staging. Protections that have never been exercised are assumptions, and interviewers know it.

---

[⬅ Back to Control Planes and Abstractions](./README.md) · [All topics](../README.md)
