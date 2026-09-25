---
title: "How do you use Argo CD ApplicationSets to manage many clusters?"
id: 88
category: "GitOps and Continuous Delivery"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - gitops-and-continuous-delivery
  - interview-questions
---

# How do you use Argo CD ApplicationSets to manage many clusters?

**Short answer:** An ApplicationSet is a template for Argo CD `Application` objects plus one or more generators that produce parameters for it. Point a cluster generator at the clusters registered in Argo CD, select them by label, and combine it with a Git generator that lists components, and the controller creates one Application per component per matching cluster - and creates or deletes them as clusters join or leave. The work at scale is not the templating; it is controlling blast radius when one commit now changes a hundred clusters, and deciding what happens when an Application is deleted.

## Detail

**The mechanism.** The ApplicationSet controller runs alongside Argo CD. It evaluates each generator, which emits a list of parameter sets; renders the template once per set; and creates, updates, or deletes the resulting Applications so they match. Argo CD then syncs those Applications as usual. The ApplicationSet is the only thing a human edits - the Applications are generated output and should be treated as such.

**The generators that matter for fleets:**

- **Cluster generator** - one parameter set per cluster Secret registered in Argo CD, filtered by a label selector. Labels on the cluster Secret (`env`, `region`, `tier`, `compliance-scope`) become the vocabulary for targeting.
- **Git generator** - one parameter set per directory or per file in a repository. Directories are a natural way to list platform components; files can hold per-cluster configuration.
- **Matrix generator** - the Cartesian product of two generators, typically clusters × components. This is the workhorse for "install every platform component on every matching cluster".
- **Merge generator** - combines generators by a key, so a base set of clusters can have per-cluster overrides layered on.
- **Others** - list, pull request (preview environments), SCM provider (every repository in an organisation), and cluster decision resource (external placement engines).

**Use Go templating.** Set `goTemplate: true` with `goTemplateOptions: ["missingkey=error"]`. The older fasttemplate `{{name}}` syntax cannot express conditionals or defaults, and silently renders an empty string for a missing label, which is how an Application ends up pointing at an overlay called `overlays/`. With `missingkey=error`, a cluster missing its `env` label fails loudly instead.

**Labels are the fleet's API.** When cluster targeting is expressed as label selectors, adding a cluster becomes registering it with the right labels, and everything it should run arrives automatically. The corollary is that cluster labels are now production configuration: a mistyped `env: prodution` either matches nothing or, worse, matches a selector you did not intend. Manage cluster Secrets through GitOps and validate their labels in CI. See [How do you keep platform components consistent across many clusters?](../kubernetes-platform/how-do-you-keep-platform-components-consistent-across-many-clusters.md).

**Blast radius: roll changes across the fleet in waves.** Without further configuration, a commit to the platform bundle updates every generated Application at once, and with automated sync every cluster changes within minutes. Two defences:

- **Pin revisions per wave.** Drive `targetRevision` from a cluster label (`bundle-version`), so moving a cluster to a new release is a label change you roll out cluster by cluster.
- **Progressive syncs.** The `RollingSync` strategy (beta since Argo CD 3.3, enabled with `--enable-progressive-syncs` on the ApplicationSet controller) syncs generated Applications in steps selected by their labels, waits for each step to become healthy before moving on, and can cap how many update at once with `maxUpdate`. It disables automated sync on the generated Applications, because the controller now decides when each one syncs. See [How do you upgrade a fleet of clusters without breaking tenants?](../kubernetes-platform/how-do-you-upgrade-a-fleet-of-clusters-without-breaking-tenants.md).

**Deletion is the dangerous edge.** If a cluster loses a label, or someone deletes the ApplicationSet, the controller deletes the generated Applications - and if those Applications carry the resources finalizer, Argo CD deletes everything they deployed. For platform components such as a CNI, a CSI driver, or cert-manager, that is an outage. Set `syncPolicy.preserveResourcesOnDeletion: true` on the ApplicationSet so deleting an Application leaves its resources in place, and consider `applicationsSync: create-update` so the controller never deletes Applications on its own. Treat label changes that remove a cluster from a selector as a reviewed operation.

**Tenancy and security.** Generated Applications should land in an `AppProject` that restricts source repositories, destination clusters, and namespaces, so a template bug cannot deploy to the wrong place. ApplicationSets can be created in namespaces other than `argocd`, but that is off by default for good reason: SCM provider and pull request generators combined with a permissive project let a tenant generate Applications targeting anything the project allows. Keep fleet-wide ApplicationSets owned by the platform team.

**Scaling the control plane.** A single Argo CD managing many clusters concentrates credentials for all of them and does a lot of work in one application controller. Shard the controller across replicas so clusters are distributed between them, tune the repository server's caching and parallelism, and watch reconciliation queue depth. Some organisations instead run Argo CD per region or per environment tier, each with its own ApplicationSets, trading a single pane of glass for smaller failure and credential domains.

**The platform user.** Two audiences benefit. Platform engineers manage one ApplicationSet per capability instead of hundreds of hand-written Applications. Product and cluster owners get a predictable contract: label a cluster `tier: standard`, and it receives the standard bundle, upgraded in the same waves as its peers.

## Example

```yaml
# A cluster registered with Argo CD. The labels are what generators select on.
apiVersion: v1
kind: Secret
metadata:
  name: prod-eu-1
  namespace: argocd
  labels:
    argocd.argoproj.io/secret-type: cluster
    platform.example.com/managed: "true"
    env: production
    region: eu-west-1
    bundle-version: v2026.09.2
type: Opaque
stringData:
  name: prod-eu-1
  server: https://prod-eu-1.example.internal
  config: |
    {
      "awsAuthConfig": {
        "clusterName": "prod-eu-1",
        "roleARN": "arn:aws:iam::<account-id>:role/argocd-deployer"
      },
      "tlsClientConfig": { "caData": "<base64-ca-bundle>" }
    }
```

```yaml
# Every platform component on every managed cluster, rolled out in waves.
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata: { name: platform-bundle, namespace: argocd }
spec:
  goTemplate: true
  goTemplateOptions: ["missingkey=error"] # a missing label fails, not renders ""
  generators:
    - matrix:
        generators:
          - clusters:
              selector:
                matchLabels: { platform.example.com/managed: "true" }
                matchExpressions:
                  - { key: env, operator: In, values: [staging, production] }
          - git:
              repoURL: https://github.com/example/platform-bundle
              revision: main # component list only; versions come from the label
              directories:
                - path: components/*
  strategy:
    type: RollingSync # requires --enable-progressive-syncs on the controller
    rollingSync:
      steps:
        - matchExpressions: [{ key: env, operator: In, values: [staging] }]
        - matchExpressions: [{ key: env, operator: In, values: [production] }]
          maxUpdate: 25% # at most a quarter of production Applications at once
  syncPolicy:
    preserveResourcesOnDeletion: true # deleting an Application never deletes the CNI
    applicationsSync: create-update # the controller never deletes Applications itself
  template:
    metadata:
      name: "{{.path.basename}}-{{.name}}"
      labels:
        env: '{{index .metadata.labels "env"}}' # RollingSync steps match on this
    spec:
      project: platform
      source:
        repoURL: https://github.com/example/platform-bundle
        targetRevision: '{{index .metadata.labels "bundle-version"}}'
        path: '{{.path.path}}/overlays/{{index .metadata.labels "env"}}'
      destination:
        server: "{{.server}}"
        namespace: "{{.path.basename}}"
      syncPolicy:
        syncOptions: [CreateNamespace=true, ServerSideApply=true]
        # no `automated` block: RollingSync triggers the syncs
```

```text
What the controller produces for three clusters and three components:

  CLUSTER        ENV         COMPONENT        APPLICATION                   STEP
  staging-eu-1   staging     cert-manager     cert-manager-staging-eu-1     1
  staging-eu-1   staging     otel-collector   otel-collector-staging-eu-1   1
  staging-eu-1   staging     policy-engine    policy-engine-staging-eu-1    1
  prod-eu-1      production  cert-manager     cert-manager-prod-eu-1        2
  prod-eu-1      production  otel-collector   otel-collector-prod-eu-1      2
  prod-eu-1      production  policy-engine    policy-engine-prod-eu-1       2
  prod-us-1      production  ...                                            2

  Register a fourth cluster with the right labels -> three more Applications,
  no pull request to the ApplicationSet at all.
```

## Interview tips

- Explain the mechanism first: generators produce parameters, the template is rendered once per parameter set, and the controller reconciles the resulting Applications.
- Name the matrix of clusters × components as the standard fleet pattern, and cluster labels as the targeting vocabulary - which makes labels production configuration that needs review.
- Bring up blast radius before you are asked. Per-cluster version labels and RollingSync progressive syncs are the two tools; know that RollingSync disables automated sync on the generated Applications.
- The deletion trap is the strongest senior signal: a label change or a deleted ApplicationSet can cascade into deleting a CNI. `preserveResourcesOnDeletion` and a `create-update` policy are the answers.
- Recommend `goTemplate: true` with `missingkey=error`, and mention controller sharding or multiple Argo CD instances when asked how this scales past a few hundred clusters. For the repository layout feeding it, see [How do you structure repositories for GitOps at scale?](./how-do-you-structure-repositories-for-gitops-at-scale.md).

---

[⬅ Back to GitOps and Continuous Delivery](./README.md) · [All topics](../README.md)
