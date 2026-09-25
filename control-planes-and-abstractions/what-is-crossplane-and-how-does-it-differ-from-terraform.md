---
title: "What is Crossplane and how does it differ from Terraform?"
id: 74
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

| Dimension              | Crossplane                                     | Terraform / OpenTofu                    |
| ---------------------- | ---------------------------------------------- | --------------------------------------- |
| Model                  | Continuous reconciliation                      | Run to completion                       |
| Drift                  | Corrected automatically                        | Detected only when a plan runs          |
| State                  | Kubernetes objects; no state file              | State backend, needs locking and backup |
| Preview before change  | Weak - no first-class plan                     | Strong - `terraform plan`               |
| Provider coverage      | Broad; many generated from Terraform providers | Very broad                              |
| Self-service interface | Native - namespaced XRs plus RBAC              | Needs a wrapper (pipeline, portal)      |
| Blast radius           | Per resource or per composite                  | Per workspace or state file             |
| Operational burden     | A control plane to run and upgrade             | A runner fleet, or a hosted service     |
| Hiring and familiarity | Narrower                                       | Very widely known                       |

**The missing plan is the most-cited weakness.** Crossplane has no first-class equivalent of `terraform plan`, so "what exactly will this change in production?" is harder to answer before it happens. Mitigations exist - rendering a composition locally with the Crossplane CLI's `render` command, dry-run and server-side apply diffs, staging environments, admission policy on dangerous fields - but this is a real gap and acknowledging it is what makes an answer credible.

**Compositions are the reason platform teams choose it.** A composite resource definition plus a composition lets you define your own abstraction - `PostgresInstance` with `size`, `backups`, and `pitr` - that expands into the underlying cloud resources with your naming, tagging, network placement, and IAM. Since Crossplane v2 (August 2025) that composite resource is namespaced by default, so teams create it directly in their namespace with no separate claim, RBAC controls who can create what, and admission policy applies to it like any other Kubernetes object. v2 compositions can also include any Kubernetes resource, so one abstraction can deploy the workload alongside its database - something Terraform would hand off to a second tool. That is a self-service infrastructure API with authorisation and audit included, which is exactly what a platform needs and what Terraform requires additional machinery to provide.

**Deletion is the sharp edge.** Because these are Kubernetes objects, deleting a composite resource deletes real infrastructure. A namespace deletion can therefore destroy a production database. This is not hypothetical and it is the single most important operational caveat: stateful resources need non-default management policies - on v2 namespaced managed resources, `managementPolicies` without `Delete`, which replaced `deletionPolicy: Orphan` - plus admission protection.

**They coexist well, and that is usually the honest recommendation.** Terraform for bootstrap and account-level infrastructure - the cloud accounts, the network foundation, and the cluster that Crossplane itself runs on, because Crossplane cannot provision its own substrate. Crossplane for the application-level resources teams request self-service. Presenting that split shows judgement rather than allegiance.

## Example

```yaml
# The platform team defines the abstraction once.
# Crossplane v2: namespaced by default, so no separate claim kind is needed.
apiVersion: apiextensions.crossplane.io/v2
kind: CompositeResourceDefinition
metadata: { name: postgresinstances.platform.example.com }
spec:
  scope: Namespaced
  group: platform.example.com
  names: { kind: PostgresInstance, plural: postgresinstances }
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
            status:
              type: object
              properties:
                connectionSecret: { type: string } # composition writes a Secret and names it here
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
# The composition writes credentials to a Secret in team-payments
# (v2 composes the Secret explicitly; XR-level connection details were removed).
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

SCENARIO B - someone deletes the namespace containing the composite
  Crossplane   the composite is deleted, and by default the database is DESTROYED.
               This is the sharp edge, and it needs guarding explicitly:
                 managementPolicies without "Delete" (on the managed resource;
                 deletionPolicy: Orphan on v1-style cluster-scoped ones)
                 + admission policy rejecting deletion of production composites
                 + a finalizer requiring an explicit approval annotation
  Terraform    the state file is unaffected; nothing happens to the database.
               Destroying it requires an explicit `terraform destroy`.

Scenario A favours Crossplane. Scenario B is why stateful resources need
deliberate protection before you put a production database behind a
composite resource.
```

## Interview tips

- "Continuous reconciliation versus run to completion" is the sentence that answers the question; every other difference follows from it.
- Volunteer the weaknesses - no first-class plan, narrower provider coverage, a control plane to operate - before you are asked. It is what distinguishes assessment from advocacy.
- The deletion hazard is the highest-value operational point. Saying that a namespace deletion can destroy a production database, and naming orphan-on-delete (`managementPolicies` without `Delete` in Crossplane v2) plus admission protection, reads as hard-won.
- Compositions plus namespaced composite resources plus RBAC as a ready-made self-service API is the platform-engineering reason to choose it - make that argument explicitly rather than listing features. Knowing that v2 dropped claims and can compose any Kubernetes resource shows your knowledge is current (see [what changed in Crossplane v2](./what-changed-in-crossplane-v2-and-why-does-it-matter.md)).
- Recommending both, with Terraform for bootstrap and account-level infrastructure because Crossplane cannot provision its own substrate, is the answer that shows judgement.

---

[⬅ Back to Control Planes and Abstractions](./README.md) · [All topics](../README.md)
