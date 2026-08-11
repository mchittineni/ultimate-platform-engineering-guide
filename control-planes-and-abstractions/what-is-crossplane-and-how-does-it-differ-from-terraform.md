---
title: "What is Crossplane and how does it differ from Terraform?"
id: 38
category: "Control Planes and Abstractions"
difficulty: "Advanced"
tags:
  - platform-engineering
  - control-planes-and-abstractions
  - interview-questions
---

# What is Crossplane and how does it differ from Terraform?

**Short answer:** Crossplane turns cloud infrastructure into Kubernetes resources managed by controllers, so provisioning is continuously reconciled rather than applied by a run. Terraform is a run-to-completion tool: it computes a plan and applies it, and between runs nothing watches. The practical differences follow from that - Crossplane corrects drift automatically and needs no state file or runner fleet, while Terraform has far broader provider coverage, an explicit reviewable plan, and a much larger pool of people who know it.

## Detail

**The core distinction is reconciliation versus run-to-completion.** A Crossplane managed resource is watched by a controller that continuously compares the cloud reality to the declared spec and corrects differences. Terraform compares only when someone runs a plan, so drift persists until the next run - and is often silently overwritten or, worse, revealed as an unexpected destroy.

**Where the state lives.** Terraform keeps state in a backend file, which must be locked, backed up, and protected; a corrupted or lost state file is a serious incident, and state manipulation is a genuinely dangerous operation. Crossplane stores desired state as Kubernetes objects in etcd and discovers actual state from the provider's API on every reconcile, so there is no separate state artefact to lose - though etcd now holds critical infrastructure records and needs backup rigour of its own.

**The comparison in the terms that decide an adoption:**

| Dimension              | Crossplane                         | Terraform / OpenTofu                    |
| ---------------------- | ---------------------------------- | --------------------------------------- |
| Model                  | Continuous reconciliation          | Run to completion                       |
| Drift                  | Corrected automatically            | Detected only when a plan runs          |
| State                  | Kubernetes objects; no state file  | State backend, needs locking and backup |
| Preview before change  | Weak - no first-class plan         | Strong - `terraform plan`               |
| Provider coverage      | Good and growing; gaps exist       | Very broad                              |
| Self-service interface | Native - claims plus RBAC          | Needs a wrapper (pipeline, portal)      |
| Blast radius           | Per resource or per claim          | Per workspace or state file             |
| Operational burden     | A control plane to run and upgrade | A runner fleet, or a hosted service     |
| Hiring and familiarity | Narrower                           | Very widely known                       |

**The missing plan is the most-cited weakness.** Crossplane has no first-class equivalent of `terraform plan`, so "what exactly will this change in production?" is harder to answer before it happens. Mitigations exist - dry-run and server-side apply diffs, staging environments, admission policy on dangerous fields - but this is a real gap and acknowledging it is what makes an answer credible.

**Compositions are the reason platform teams choose it.** A composite resource definition plus a composition lets you define your own abstraction - `PostgresInstance` with `size`, `backups`, and `pitr` - that expands into the underlying cloud resources with your naming, tagging, network placement, and IAM. Teams file a namespaced claim, RBAC controls who can claim what, and admission policy applies to it like any other Kubernetes object. That is a self-service infrastructure API with authorisation and audit included, which is exactly what a platform needs and what Terraform requires additional machinery to provide.

**Deletion is the sharp edge.** Because these are Kubernetes objects, deleting a claim deletes real infrastructure. A namespace deletion can therefore destroy a production database. This is not hypothetical and it is the single most important operational caveat: stateful resources need a non-default deletion policy plus admission protection.

**They coexist well, and that is usually the honest recommendation.** Terraform for bootstrap and account-level infrastructure - the cloud accounts, the network foundation, and the cluster that Crossplane itself runs on, because Crossplane cannot provision its own substrate. Crossplane for the application-level resources teams request self-service. Presenting that split shows judgement rather than allegiance.

## Example

```yaml
# The platform team defines the abstraction once.
apiVersion: apiextensions.crossplane.io/v1
kind: CompositeResourceDefinition
metadata: { name: xpostgresinstances.platform.example.com }
spec:
  group: platform.example.com
  names: { kind: XPostgresInstance, plural: xpostgresinstances }
  claimNames: { kind: PostgresInstance, plural: postgresinstances } # namespaced claim
  versions:
    - name: v1
      served: true
      referenceable: true
      schema:
        openAPIV3Schema:
          type: object
          properties:
            spec:
              type: object
              required: [size]
              properties:
                size: { type: string, enum: [small, medium, large] }
                backups: { type: string, enum: [none, daily, hourly], default: daily }
                pitr: { type: boolean, default: true }
```

```yaml
# A developer's entire interaction. Namespaced, RBAC-controlled, auditable,
# and subject to the same admission policies as any other Kubernetes object.
apiVersion: platform.example.com/v1
kind: PostgresInstance
metadata: { name: checkout-db, namespace: team-payments }
spec:
  size: small
  pitr: true
  writeConnectionSecretToRef: { name: checkout-db-conn } # credentials land here
```

```text
Two failure scenarios, which is where the models genuinely diverge:

SCENARIO A - someone changes the database instance class in the cloud console
  Crossplane   controller observes the difference on its next reconcile and
               reverts it within a minute. An event is emitted. Drift is not
               possible for long.
  Terraform    nothing happens. The change persists until the next plan, which
               then shows an unexpected diff - and if run with -auto-approve in
               a pipeline, silently reverts it with no human seeing the surprise.

SCENARIO B - someone deletes the namespace containing the claim
  Crossplane   the claim is deleted, and by default the database is DESTROYED.
               This is the sharp edge, and it needs guarding explicitly:
                 spec.deletionPolicy: Orphan  (on the managed resource)
                 + admission policy rejecting deletion of production claims
                 + a finalizer requiring an explicit approval annotation
  Terraform    the state file is unaffected; nothing happens to the database.
               Destroying it requires an explicit `terraform destroy`.

Scenario A favours Crossplane. Scenario B is why stateful resources need
deliberate protection before you put a production database behind a claim.
```

## Interview tips

- "Continuous reconciliation versus run to completion" is the sentence that answers the question; every other difference follows from it.
- Volunteer the weaknesses - no first-class plan, narrower provider coverage, a control plane to operate - before you are asked. It is what distinguishes assessment from advocacy.
- The deletion hazard is the highest-value operational point. Saying that a namespace deletion can destroy a production database, and naming `deletionPolicy: Orphan` plus admission protection, reads as hard-won.
- Compositions plus claims plus RBAC as a ready-made self-service API is the platform-engineering reason to choose it - make that argument explicitly rather than listing features.
- Recommending both, with Terraform for bootstrap and account-level infrastructure because Crossplane cannot provision its own substrate, is the answer that shows judgement.

---

[⬅ Back to Control Planes and Abstractions](./README.md) · [All topics](../README.md)
