---
title: "How do you keep platform components consistent across many clusters?"
id: 65
category: "Kubernetes Platform"
difficulty: "Advanced"
tags:
  - platform-engineering
  - kubernetes-platform
  - interview-questions
---

# How do you keep platform components consistent across many clusters?

**Short answer:** Define the platform's contents once as a versioned bundle, label every cluster with its properties, and have a reconciler apply the bundle to clusters selected by those labels - so a cluster's contents are derived from what it _is_, not from what someone remembered to install. Then roll bundle versions out in waves with a per-cluster version recorded, and continuously report drift. The alternative, installing components per cluster, produces a fleet where no two clusters are the same and none can be upgraded confidently.

## Detail

**The failure mode this prevents.** Components installed cluster by cluster diverge immediately: different Helm values, different versions, a fix applied to three clusters out of nine. Six months later nobody knows what any given cluster contains, upgrades become bespoke investigations, and an incident in one cluster cannot be reasoned about from another. This is the single most common way a growing fleet becomes unmaintainable.

**Define the platform as a versioned artefact.** One repository declares every component the platform consists of, with pinned versions and configuration - ingress controller, cert-manager, CSI drivers, telemetry agents, policy engine and bundle, secrets driver, base namespaces, RBAC, priority classes, default network policies. That artefact has a version, and a cluster runs a specific version of it. "Platform v2026.08.1" becomes a thing you can talk about, test, and roll back.

**Select by label, not by name.** Every cluster carries labels for environment, region, compliance scope, tenancy model, and upgrade channel. The bundle definition targets those labels: production clusters get this policy set, PCI clusters get additional controls, EU clusters get a specific log destination. A new cluster created with the right labels becomes correct automatically, which is what makes cluster creation reproducible.

**Handle variation explicitly, and keep it small.** Some differences are legitimate - region-specific endpoints, different replica counts by environment, extra controls in a compliance scope. Model these as parameters resolved from cluster labels, and treat any per-cluster special case as a finding to be either generalised into a property or removed. Unmodelled variation is how consistency erodes.

**Argo CD ApplicationSets or Flux with a cluster inventory are the usual mechanisms.** The generator enumerates clusters from the inventory and produces one application per cluster per component. What matters more than the tool is that the source of truth is the fleet definition, and that adding a cluster to the inventory is the only action required to make it fully provisioned.

**Roll out in waves and record the version per cluster.** Bundle upgrades are staged the same way Kubernetes upgrades are - dev, staging, low-tier production, high-tier production, management last - with soak time and abort criteria. Recording the running bundle version per cluster is what makes the fleet's state answerable in one query, and it is what lets you say "the problem is in v2026.08.1, and four clusters have it".

**Report drift continuously, in both directions.** Anything present in a cluster that is not in the bundle, and anything in the bundle missing from a cluster. Emergency manual changes are legitimate during an incident and illegitimate afterwards; drift reporting is how the temporary fix gets promoted into the bundle or removed rather than quietly becoming a permanent undocumented difference.

**Bootstrapping needs an answer.** Something must install the reconciler on a brand-new cluster before the reconciler can manage it. Keep that seed step minimal, automated, and documented - typically the cluster provisioning pipeline installs the GitOps agent and registers the cluster, after which everything else follows.

## Example

```yaml
# The fleet definition: one component, applied to clusters selected by property.
# A new cluster with matching labels gets this automatically.
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata: { name: platform-policy-engine, namespace: argocd }
spec:
  goTemplate: true # Go templates: the recommended syntax in current Argo CD
  goTemplateOptions: ["missingkey=error"] # a missing label fails loudly
  generators:
    - clusters:
        selector:
          matchLabels:
            platform.example.com/managed: "true"
  template:
    metadata:
      name: "policy-engine-{{.name}}"
    spec:
      project: platform
      source:
        repoURL: https://github.com/example/platform-bundle
        # Pinned, and moved per wave - never a floating branch
        targetRevision: v2026.08.1
        path: components/policy-engine
        helm:
          valueFiles:
            - values/base.yaml
            # Variation resolved from cluster labels, not per-cluster files
            - 'values/env-{{ index .metadata.labels "platform.example.com/environment" }}.yaml'
            - 'values/scope-{{ index .metadata.labels "platform.example.com/compliance-scope" }}.yaml'
      destination: { server: "{{.server}}", namespace: policy-system }
      syncPolicy:
        automated: { prune: true, selfHeal: true } # selfHeal reverts manual drift
```

```text
Fleet state - answerable in one query, which is the point of the whole design:

  $ platform fleet status

  CLUSTER            ENV      SCOPE     BUNDLE        DRIFT   K8S
  mgmt-eu-1          mgmt     standard  v2026.07.3    0       1.35
  mgmt-eu-2          mgmt     standard  v2026.07.3    0       1.35
  prod-eu-1          prod     standard  v2026.08.1    0       1.36
  prod-eu-2          prod     standard  v2026.08.1    2  <--  1.36
  prod-us-1          prod     standard  v2026.08.1    0       1.36
  prod-pci-eu-1      prod     pci       v2026.07.3    0       1.35
  staging-eu-1       staging  standard  v2026.08.2    0       1.36
  dev-eu-1           dev      standard  v2026.08.2    0       1.36
  preview-eu-1       dev      standard  v2026.08.2    0       1.36

  Wave in progress: v2026.08.2 in dev/staging, soaking. prod on v2026.08.1.
  mgmt intentionally trails - it is upgraded last.

  $ platform fleet drift prod-eu-2
    EXTRA    DaemonSet/debug-tcpdump (kube-system)
             created 2026-08-09 by alice during INC-2291
             -> decide: promote into the bundle, or remove
    MISSING  NetworkPolicy/default-deny (team-legacy)
             deleted 2026-08-10 by bob
             -> selfHeal will restore it; investigate why it was removed

  Both directions reported. This is how an incident-time fix either becomes
  policy or gets cleaned up, instead of silently becoming a permanent difference.
```

## Interview tips

- The core idea to land: a cluster's contents are derived from its labels, not from an install history. That is what makes cluster creation reproducible and upgrades confident.
- "The platform has a version" is a powerful reframing - it turns fleet management into something you can test, wave, and roll back.
- Label-based selection over name-based targeting is the specific mechanism; mention ApplicationSets or Flux with a cluster inventory as the implementation, but emphasise the definition is the source of truth.
- Bidirectional drift reporting, and specifically the incident-time manual change that must be promoted or removed, is the operationally honest detail interviewers respond to.
- Volunteer the bootstrapping problem - something must install the reconciler before it can manage the cluster - and keep that step minimal and automated.

---

[⬅ Back to Kubernetes Platform](./README.md) · [All topics](../README.md)
