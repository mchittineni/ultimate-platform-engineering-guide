---
title: "What changed in Crossplane v2 and why does it matter?"
id: 72
category: "Control Planes and Abstractions"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - control-planes-and-abstractions
  - interview-questions
---

# What changed in Crossplane v2 and why does it matter?

**Short answer:** Crossplane v2, released in August 2025, made composite resources (XRs) and managed resources namespaced by default, dropped the need for claims, and let a composition include any Kubernetes resource - a Deployment or a Service as easily as a cloud database. Composition functions became the only way to compose, and several v1 features were removed. It matters because it turns Crossplane from "infrastructure behind a claim" into a general way to build platform APIs that span applications and infrastructure, with ordinary namespace-based tenancy.

## Detail

**The v1 model and its friction.** In v1, composite resources were cluster-scoped, so to give teams a namespaced API you defined a separate _claim_ kind that pointed at a cluster-scoped XR, which in turn owned cluster-scoped managed resources. Every abstraction existed twice (claim and XR), tenancy relied on the claim's namespace alone, and compositions were in practice limited to Crossplane managed resources. Deploying the application alongside its database needed a second tool.

**Namespaced XRs, no claims.** The v2 `CompositeResourceDefinition` (`apiextensions.crossplane.io/v2`) has a `scope` field that defaults to `Namespaced`. A developer creates the XR directly in their namespace - there is no claim layer. A namespaced XR can only compose resources in its own namespace, so the tenancy boundary is enforced by Kubernetes itself. The other scopes are `Cluster`, for genuinely cluster-wide abstractions, and `LegacyCluster`, which keeps v1-style XRs and claims working.

**Namespaced managed resources.** Providers now ship namespaced versions of their managed resources, in new API groups with an `.m.` in them - `s3.aws.m.upbound.io` rather than `s3.aws.upbound.io`. Connection secrets land in the same namespace. Provider credentials are split into a namespaced `ProviderConfig` and a cluster-wide `ClusterProviderConfig`, so a tenant can be pinned to its own cloud account. The old cluster-scoped managed resources still work but are deprecated.

**Compose anything.** A composition can now include any Kubernetes resource: Deployments, Services, HTTPRoutes, ConfigMaps, or other operators' custom resources. A single `App` XR can render the workload, its gateway route, and its cloud database, and Crossplane reconciles all of them. This puts Crossplane in the same space as kro and makes it a candidate for the whole platform API, not just the infrastructure part.

**Functions only.** The native patch-and-transform composition mode is gone; every composition runs in `Pipeline` mode through composition functions. Patch-and-transform survives as a function, alongside functions for Go templates, KCL, Python, and CEL. Existing v1 compositions using native patch-and-transform must be converted before upgrading.

**Other breaking changes worth knowing:**

- `ControllerConfig` removed - use `DeploymentRuntimeConfig`.
- External secret stores removed.
- XR-level connection details removed - compose a Secret explicitly if you need one.
- `deletionPolicy` does not exist on namespaced managed resources; use `managementPolicies` (omitting `Delete` orphans the external resource).
- Crossplane's own machinery fields on an XR moved under `spec.crossplane` (for example `spec.crossplane.compositionRef`).
- Package references must be fully qualified (`xpkg.crossplane.io/...`); the default registry flag is gone.

**Operations.** v2 also added an alpha `Operation` type, with `CronOperation` and `WatchOperation`, which runs a function pipeline to completion like a Job. It is aimed at day-two tasks - backups, certificate checks, upgrade gates - that do not fit a continuous reconcile.

**Why it matters for a platform team.** Tenancy becomes plain Kubernetes: namespace RBAC, quotas, and admission policies apply directly to the resources developers create. The API surface halves because there is no claim/XR pair to maintain. And application plus infrastructure in one abstraction reduces the number of tools a developer has to learn. The trade-offs are the migration work - removed features, new API groups for managed resources, and different deletion semantics - and the continued absence of a first-class plan.

## Example

```yaml
# A v2 XRD: namespaced by default, no claimNames.
apiVersion: apiextensions.crossplane.io/v2
kind: CompositeResourceDefinition
metadata:
  name: apps.platform.example.com
spec:
  scope: Namespaced
  group: platform.example.com
  names: { kind: App, plural: apps }
  versions:
    - name: v1alpha1
      served: true
      referenceable: true
      schema:
        openAPIV3Schema:
          type: object
          properties:
            spec:
              type: object
              required: [image]
              properties:
                image: { type: string }
```

```yaml
# A composition that mixes a plain Deployment with a namespaced managed resource.
apiVersion: apiextensions.crossplane.io/v1
kind: Composition
metadata:
  name: app-aws
spec:
  compositeTypeRef:
    apiVersion: platform.example.com/v1alpha1
    kind: App
  mode: Pipeline
  pipeline:
    - step: render
      functionRef: { name: function-patch-and-transform }
      input:
        apiVersion: pt.fn.crossplane.io/v1beta1
        kind: Resources
        resources:
          - name: deployment
            base:
              apiVersion: apps/v1
              kind: Deployment
              spec:
                replicas: 2
                selector: { matchLabels: { app: web } }
                template:
                  metadata: { labels: { app: web } }
                  spec:
                    containers:
                      - name: web
                        image: nginx # replaced by the patch below
            patches:
              - type: FromCompositeFieldPath
                fromFieldPath: spec.image
                toFieldPath: spec.template.spec.containers[0].image
          - name: assets
            base:
              apiVersion: s3.aws.m.upbound.io/v1beta1 # namespaced MR
              kind: Bucket
              spec:
                forProvider: { region: eu-west-1 }
                # orphan on delete: no "Delete" in the list
                managementPolicies: ["Create", "Observe", "Update", "LateInitialize"]
    - step: ready
      functionRef: { name: function-auto-ready }
```

```yaml
# The developer's whole interaction - created directly in their namespace.
apiVersion: platform.example.com/v1alpha1
kind: App
metadata:
  name: checkout
  namespace: team-payments
spec:
  image: ghcr.io/example/checkout:1.4.2
```

## Interview tips

- Lead with the three headline changes: namespaced XRs and managed resources, no claims needed, and compositions that can include any Kubernetes resource.
- Explain why namespacing matters: tenancy, RBAC, and quotas now work on the resources developers actually create, with no claim indirection.
- Know the breaking changes, especially native patch-and-transform being replaced by functions and `deletionPolicy` giving way to `managementPolicies` on namespaced resources - a migration question often follows.
- Note that v1-style XRs and claims keep working as `LegacyCluster`, so upgrades can be incremental once removed features are gone - the v1.20 CLI's `crossplane beta upgrade check` reports what would break.
- Expect a comparison with kro or Terraform next; "compose anything" puts Crossplane v2 directly alongside kro, and the missing plan is still the main contrast with Terraform (see [Crossplane versus Terraform](./what-is-crossplane-and-how-does-it-differ-from-terraform.md)).

---

[⬅ Back to Control Planes and Abstractions](./README.md) · [All topics](../README.md)
