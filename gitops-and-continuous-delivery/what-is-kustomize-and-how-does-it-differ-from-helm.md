---
title: "What is Kustomize and how does it differ from Helm?"
id: 82
category: "GitOps and Continuous Delivery"
difficulty: "Beginner"
tags:
  - platform-engineering
  - gitops-and-continuous-delivery
  - interview-questions
---

# What is Kustomize and how does it differ from Helm?

**Short answer:** Kustomize customises plain Kubernetes YAML without templates. You write ordinary, valid manifests as a _base_, then describe per-environment differences as _overlays_ that patch the base - change the replica count, add a label, swap an image. Helm takes the opposite approach: it generates manifests from templates filled in with values, and it also tracks installed releases. Kustomize is usually the better fit for your own services' environment variations; Helm is usually the better fit for packaging software that many different users will install.

## Detail

**The core idea: patch, do not template.** Every file in a Kustomize base is a real Kubernetes manifest that you could `kubectl apply` on its own. A `kustomization.yaml` lists those resources and the transformations to apply. An overlay is another directory with its own `kustomization.yaml` that points at the base and adds patches. Running `kustomize build` (or `kubectl kustomize`, since it is built into kubectl) produces the final YAML. Nothing is interpolated into strings; changes are structural edits to parsed objects.

**The main building blocks:**

- **`resources`** - the manifests or other kustomizations to include. This replaced the older `bases` field.
- **`patches`** - strategic-merge or JSON 6902 patches, optionally targeted by kind, name, or label selector. This single field replaced the deprecated `patchesStrategicMerge` and `patchesJson6902`; `kustomize edit fix` rewrites old files.
- **`images`** - override an image name, tag, or digest without writing a patch. This is how CI usually promotes a new build.
- **`labels`** and **`namespace`** - apply labels or a namespace to everything. `labels` replaced the deprecated `commonLabels`, which also rewrote selectors and caused painful immutable-field errors.
- **`configMapGenerator`** and **`secretGenerator`** - build ConfigMaps from files and append a content hash to the name, so changing config forces a rolling restart.
- **`components`** - reusable, optional bundles of patches (for example "enable-tracing") that several overlays can opt into.

**How it differs from Helm, in practice:**

| Question                      | Kustomize                               | Helm                                          |
| ----------------------------- | --------------------------------------- | --------------------------------------------- |
| How are variations expressed? | Patches over valid YAML                 | Values injected into Go templates             |
| Is the source valid YAML?     | Yes, always                             | No - templates only become YAML when rendered |
| Release tracking / rollback   | None; it only renders                   | Releases, `helm rollback`, hooks              |
| Packaging and distribution    | Directories or Git URLs                 | Versioned charts in OCI registries            |
| Logic (loops, conditionals)   | None by design                          | Full templating language                      |
| Best at                       | Your own apps across a few environments | Third-party software with many consumers      |

**Why "no logic" is a feature.** Kustomize deliberately has no conditionals or loops. That makes it more verbose when you need genuine variation, but it means a reviewer can read a patch and know exactly which field changes. With Helm, a single value can flow through several `if` blocks and change objects you did not expect.

**Why Helm still wins for distribution.** If you publish software for other people, they need a stable interface - "set `ingress.enabled: true`" - rather than having to know your manifests well enough to patch them. Helm's values are that interface, and its versioned charts are the delivery mechanism. Kustomize has no concept of a package version beyond a Git reference.

**They combine well.** A common pattern is to render a third-party Helm chart and then apply Kustomize patches on top for the last few changes the chart does not expose. Kustomize can do this itself with the `helmCharts` field (`kustomize build --enable-helm`), Argo CD supports the same thing once `--enable-helm` is added to its Kustomize build options, and Flux's `HelmRelease` supports Kustomize-style `postRenderers`. Use this sparingly: two layers of transformation are harder to reason about than one.

**The trade-offs.** Kustomize overlays can sprawl - deep chains of overlays inheriting from overlays are as hard to follow as a complicated chart. Its patch syntax for lists (containers, env vars) trips people up, and it cannot express "one Deployment per item in this list". Keep the hierarchy shallow: one base, one overlay per environment, and components for optional features.

**The platform user.** Product engineers usually meet Kustomize in their team's deployment repository: a base for each service plus `dev`, `staging`, and `production` overlays. The platform's job is to give them a standard layout and a CI check that runs `kustomize build` for every overlay and validates the output, so a broken patch fails in the pull request rather than at sync time. Both Argo CD and Flux build Kustomize natively; Flux's reconciler is literally called a `Kustomization`. See [How do you structure repositories for GitOps at scale?](./how-do-you-structure-repositories-for-gitops-at-scale.md).

## Example

```text
checkout-deploy/
  base/
    deployment.yaml
    service.yaml
    kustomization.yaml
  overlays/
    staging/
      kustomization.yaml
    production/
      kustomization.yaml
      replicas-patch.yaml
```

```yaml
# base/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - deployment.yaml
  - service.yaml
labels:
  - pairs: { app.kubernetes.io/name: checkout }
    includeSelectors: false # labels only; never rewrite immutable selectors
```

```yaml
# overlays/production/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
namespace: team-payments
resources:
  - ../../base
images:
  - name: ghcr.io/example/checkout
    digest: sha256:9f2c8b1d4e6a... # CI updates this line on promotion
patches:
  - path: replicas-patch.yaml
  - target: { kind: Deployment, name: checkout }
    patch: |-
      - op: add
        path: /spec/template/spec/containers/0/env/-
        value: { name: LOG_LEVEL, value: warn }
configMapGenerator:
  - name: checkout-config
    files: [config/app.yaml] # name gets a hash suffix; a change triggers a rollout
```

```yaml
# overlays/production/replicas-patch.yaml - a strategic-merge patch is just partial YAML.
apiVersion: apps/v1
kind: Deployment
metadata: { name: checkout }
spec:
  replicas: 6
```

```bash
kubectl kustomize overlays/production          # render and inspect
kubectl diff -k overlays/production            # compare with the live cluster
cd overlays/production && kustomize edit set image \
  ghcr.io/example/checkout@sha256:4a1e77c2...   # how CI bumps the digest
```

## Interview tips

- Lead with "patches over valid YAML versus templates filled with values" - it is the one-sentence difference and everything else follows from it.
- Point out that Kustomize only renders; it has no releases, rollback, or hooks. In GitOps that gap is filled by the reconciler and Git history.
- Show you know current syntax: `patches` instead of `patchesStrategicMerge`, `labels` instead of `commonLabels`, `resources` instead of `bases`.
- Give a practical rule of thumb: Helm for software you distribute or consume from others, Kustomize for your own services across environments, and both together for a third-party chart that needs a few extra patches.
- Expect "what goes wrong at scale?" Deep overlay chains and awkward list patches. Keeping the hierarchy shallow and validating every rendered overlay in CI is the answer. For the Helm side, see [What is Helm and what problem does it solve?](./what-is-helm-and-what-problem-does-it-solve.md).

---

[⬅ Back to GitOps and Continuous Delivery](./README.md) · [All topics](../README.md)
