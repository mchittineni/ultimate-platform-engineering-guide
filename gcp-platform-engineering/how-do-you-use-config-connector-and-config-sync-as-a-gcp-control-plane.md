---
title: "How do you use Config Connector and Config Sync as a GCP control plane?"
id: 183
category: "GCP Platform Engineering"
difficulty: "Advanced"
tags:
  - platform-engineering
  - gcp-platform-engineering
  - interview-questions
---

# How do you use Config Connector and Config Sync as a GCP control plane?

**Short answer:** Config Connector turns GCP resources into Kubernetes custom resources reconciled by controllers, and Config Sync reconciles those resources from Git into one or many clusters. Together they give you a GitOps control plane for GCP infrastructure with continuous drift correction, Kubernetes RBAC on infrastructure requests, and admission control - so a team can declare a database in Git and get one, with your policies applied and no cloud credentials handed out.

## Detail

**Config Connector is Crossplane's Google-native equivalent.** GCP resources become custom resources - `SQLInstance`, `PubSubTopic`, `StorageBucket` - watched by controllers that continuously reconcile the real resource to the declared spec. Drift made in the console is corrected on the next loop, which is the fundamental difference from run-to-completion tooling. It is installed as a GKE add-on, which is convenient, and it authenticates to GCP through Workload Identity so no key exists.

**Config Sync is the reconciliation-from-Git half.** It watches a source - a Git repository, an OCI image, or a Helm chart, typically in Artifact Registry - and applies its contents to clusters. It supports a root source managed by the platform (`RootSync`) plus per-namespace sources owned by teams (`RepoSync`), which maps neatly onto a platform-and-tenants split. Use the `unstructured` source format: the older `hierarchy` format still works but Google now recommends against it, and Kustomize or Helm rendering covers the same need more flexibly.

**Config Sync is no longer an add-on SKU.** Since September 2025 the capabilities that were sold as GKE Enterprise - fleets, Config Sync, Policy Controller - are part of the base GKE offering, so this design no longer needs a separate licensing conversation. From version 1.20 Config Sync is installed standalone, without the old ConfigManagement Operator, and is best enabled as a fleet-level default so every registered cluster gets the same configuration.

**Together they give you one control plane for compute and infrastructure.** A team's repository contains both their workload and their `SQLInstance`, both reconciled by the same mechanism, both subject to the same RBAC and admission policies. That uniformity is the real argument: you have one interface, one audit trail, and one policy engine covering everything rather than Kubernetes for workloads and something else for cloud resources.

**Abstract with composition, do not expose raw resources.** Handing teams `SQLInstance` directly means exposing every GCP field and losing your defaults. Better to define your own `PostgresInstance` custom resource and expand it - into a `SQLInstance` plus a `SQLUser`, private networking, backup configuration, labels, and IAM - so intent is what teams write and policy is what the expansion applies. Config Connector is the engine; your abstraction is the product.

**Deletion is the sharp edge, exactly as with any reconciling control plane.** Deleting a resource deletes real infrastructure, and a namespace deletion can therefore destroy a production database. Config Connector supports an abandon deletion policy via annotation, which should be set on everything stateful, backed by admission policy rejecting deletion of production claims and by the Config Sync annotation `client.lifecycle.config.k8s.io/deletion: detach`, which stops Config Sync deleting the object when it disappears from the source.

**Understand the two resource-level ownership models.** Config Connector can create and manage a resource, or acquire an existing one. Acquisition is useful for bringing existing infrastructure under management, but it needs care: acquiring a resource and then having a slightly different spec means the controller will change production infrastructure to match. Import deliberately, with the spec verified against reality first.

**The honest weaknesses.** No first-class plan, so previewing exactly what a change will do is harder than with plan-based tooling. Resource coverage is good but not complete, so you will need an escape route for anything unsupported. And you have made a GKE cluster a dependency for provisioning - acceptable for a control-plane function, but it needs its own reliability and a documented break-glass. Config Controller, Google's hosted bundle of Config Connector, Config Sync, and Policy Controller, removes the need to run that cluster yourself.

**Keep Terraform for the bootstrap layer.** Config Connector cannot create the project, the network, or the cluster it runs in. Terraform for the foundation, Config Connector for the resources teams request self-service, is the pragmatic and defensible division.

## Example

```yaml
# What the platform defines - the abstraction teams actually use.
apiVersion: platform.example.com/v1
kind: PostgresInstance
metadata: { name: checkout-db, namespace: team-payments }
spec:
  size: small
  backups: daily
  pitr: true
```

```yaml
# What the expansion produces. The commented lines are the policy, applied
# unconditionally, with no field in the claim to override them.
apiVersion: sql.cnrm.cloud.google.com/v1beta1
kind: SQLInstance
metadata:
  name: psql-team-payments-checkout
  namespace: team-payments
  annotations:
    # Deleting the claim must NOT destroy the database. Non-negotiable for
    # anything stateful - a namespace deletion would otherwise drop production.
    cnrm.cloud.google.com/deletion-policy: abandon
    # And Config Sync must not delete this object if it vanishes from Git.
    client.lifecycle.config.k8s.io/deletion: detach
    cnrm.cloud.google.com/project-id: checkout-prod
spec:
  databaseVersion: POSTGRES_16
  region: europe-west1
  settings:
    tier: db-custom-2-7680 # from size: small - a platform decision
    availabilityType: ZONAL
    # --- mandatory; no claim field exposes these ---
    ipConfiguration:
      ipv4Enabled: false # private only
      privateNetworkRef: { external: projects/vpc-host-prod/global/networks/shared-prod }
    backupConfiguration:
      enabled: true
      pointInTimeRecoveryEnabled: true
      transactionLogRetentionDays: 7
    databaseFlags:
      - { name: cloudsql.iam_authentication, value: "on" } # no password needed
    deletionProtectionEnabled: true
    # ----------------------------------------------
  userLabels:
    managed-by: platform
    tenant: team-payments
    workload: checkout
```

```yaml
# Config Sync: a platform root source plus per-team repositories, which maps
# onto the platform-and-tenants split.
apiVersion: configsync.gke.io/v1beta1
kind: RootSync
metadata: { name: platform-root, namespace: config-management-system }
spec:
  sourceFormat: unstructured # hierarchy is still supported but discouraged
  sourceType: oci
  oci:
    # CI renders and pushes the platform config as an OCI artifact.
    image: europe-docker.pkg.dev/control-plane/config/platform-root:v2026.08.1 # pinned, moved per wave
    dir: clusters/prod-eu-1
    # Workload Identity Federation for GKE - the reconciler's own Kubernetes
    # service account is granted Artifact Registry read. No key, no Secret.
    auth: k8sserviceaccount
---
apiVersion: configsync.gke.io/v1beta1
kind: RepoSync
metadata: { name: repo-sync, namespace: team-payments }
spec:
  sourceType: git
  git:
    repo: https://github.com/example/team-payments-deploy
    revision: main
    dir: envs/production
    auth: githubapp # short-lived installation tokens rather than a personal token
    secretRef: { name: github-app-team-payments }
  # Reconciles with only the RBAC granted in this namespace, so a team cannot
  # escalate beyond it.
```

```text
The division of labour, and the deletion guard:

  TERRAFORM (bootstrap - Config Connector cannot create its own substrate)
    organisation, folders, org policies
    projects, Shared VPC host + subnets + secondary ranges
    the GKE cluster that runs Config Connector and Config Sync
    Config Connector's own Workload Identity binding

  CONFIG CONNECTOR + CONFIG SYNC (everything teams request self-service)
    databases, buckets, topics, subscriptions, service accounts, IAM bindings
    reconciled continuously; console drift corrected within a loop

  DELETION GUARD - four layers, because each has a bypass
    1. deletion-policy: abandon on every stateful resource
    2. deletionProtectionEnabled on the GCP resource itself
    3. admission policy rejecting DELETE of production claims without an
       explicit approval annotation
    4. client.lifecycle.config.k8s.io/deletion: detach, so Config Sync
       never prunes a stateful object that disappears from the source
```

## Interview tips

- Describe the two halves precisely: Config Connector reconciles GCP resources as custom resources, Config Sync reconciles those resources from Git. Many candidates blur them.
- The strongest argument is uniformity: one interface, one RBAC model, one admission policy, and one audit trail covering both workloads and infrastructure.
- "Config Connector is the engine, your abstraction is the product" - exposing raw `SQLInstance` to teams loses your defaults and your policy.
- The deletion hazard is the highest-value operational point. A namespace deletion destroying a production database is the failure to name, with `deletion-policy: abandon` plus admission protection plus Config Sync's `detach` annotation as the layered answer.
- Mention the acquisition model and its risk: importing an existing resource with a slightly different spec means the controller changes production to match.
- Volunteer the weaknesses - no first-class plan, incomplete resource coverage, a cluster now on the provisioning path - before being asked.
- Keeping Terraform for the bootstrap layer, because Config Connector cannot create its own substrate, is the practical close that shows judgement rather than allegiance.

---

[⬅ Back to GCP Platform Engineering](./README.md) · [All topics](../README.md)
