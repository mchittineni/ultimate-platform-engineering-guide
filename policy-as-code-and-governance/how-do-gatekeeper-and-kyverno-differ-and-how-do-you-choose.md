---
title: "How do Gatekeeper and Kyverno differ, and how do you choose?"
id: 139
category: "Policy as Code and Governance"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - policy-as-code-and-governance
  - interview-questions
---

# How do Gatekeeper and Kyverno differ, and how do you choose?

**Short answer:** Gatekeeper is OPA's Kubernetes integration and expresses policy in Rego, a general-purpose policy language that is powerful and has a real learning curve. Kyverno expresses policy as Kubernetes resources, and its current policy types (`ValidatingPolicy`, `MutatingPolicy`, `GeneratingPolicy` and friends) use CEL, the same expression language as Kubernetes' native admission policies. It also generates and mutates resources, not just validates them. For Kubernetes-only policy most teams should pick Kyverno; choose Gatekeeper when you need Rego's expressiveness or already use OPA for policy beyond Kubernetes. Either way, simple validation increasingly runs as native ValidatingAdmissionPolicy (GA since Kubernetes 1.30), which both engines can now generate.

## Detail

**The fundamental difference is the language, and it drives adoption.** Rego is a declarative query language for policy - genuinely powerful, capable of complex logic and cross-resource reasoning, and unfamiliar to almost everyone. Kyverno policies are Kubernetes resources whose logic is written in CEL, the expression language Kubernetes itself uses for ValidatingAdmissionPolicy and CRD validation, so a platform engineer who knows one can read the other. In practice the language determines whether anyone other than the policy author can maintain the policy set, which matters more than raw expressiveness for most estates.

**Kyverno has moved to CEL, and the legacy format is going away.** Kyverno's original `ClusterPolicy` and `Policy` types (`kyverno.io/v1`) used YAML pattern matching and JMESPath. Since 1.14 it has added CEL-based types under `policies.kyverno.io`: `ValidatingPolicy` and `ImageValidatingPolicy`, then `MutatingPolicy`, `GeneratingPolicy`, and `DeletingPolicy`, with namespaced variants. They were promoted to `v1` in 1.17, and Kyverno 1.19 (August 2026) deprecated `ClusterPolicy` and `Policy`, with removal planned for 1.20. Any new Kyverno policy should use the CEL types, and an existing estate needs a migration plan; the CLI's existing tests can be reused against migrated policies.

**OPA 1.0 changed Rego too.** OPA 1.0 made Rego v1 syntax the default (`if` and `contains` are mandatory; `in`, `some`, and `every` need no import). Gatekeeper still defaults ConstraintTemplates to v0 syntax for compatibility and makes v1 opt-in per template with `source.version: "v1"`, so new templates should opt in and old ones should be migrated before v0 support narrows.

**Kyverno does more than validate.** It validates, mutates, and generates. Mutation is what lets you implement guardrails rather than gates - injecting a security context or a default rather than rejecting the workload. Generation creates resources in response to others, for example producing a default network policy and a resource quota whenever a namespace appears. Gatekeeper's focus is validation, with mutation available but less central.

| Dimension               | Gatekeeper (OPA)              | Kyverno                        |
| ----------------------- | ----------------------------- | ------------------------------ |
| Language                | Rego (v1 opt-in per template) | CEL in Kubernetes resources    |
| Learning curve          | Steep                         | Shallow                        |
| Validate                | Yes                           | Yes                            |
| Mutate                  | Yes, secondary                | Yes, first-class               |
| Generate resources      | No                            | Yes                            |
| Image verification      | Via external data / custom    | Built-in, including provenance |
| Cross-resource logic    | Strong                        | Resource lookups from CEL      |
| Beyond Kubernetes       | Yes - OPA is general purpose  | Kubernetes-focused             |
| Audit of existing state | Yes                           | Yes                            |
| Testing tooling         | `opa test`, `gator verify`    | `kyverno test` with fixtures   |
| Generate native VAP     | Yes, from CEL templates       | Yes, from `ValidatingPolicy`   |

**Where Gatekeeper is genuinely the better answer.** If you already run OPA for API authorisation, Terraform policy, or service-level decisions, using one policy language across all of them is a real benefit - the skills, tests, and libraries transfer. Rego also handles complex logic and reasoning across multiple resources more comfortably. And if your policies need external data, OPA's model for that is more established.

**Where Kyverno wins.** Kubernetes-only estates, teams without Rego expertise, and any case where you want mutation and generation as first-class tools. Built-in image signature and provenance verification is a notable practical advantage, because supply-chain admission verification is one of the highest-value policies a platform runs and having it built in is much simpler than assembling it.

**Do not forget the built-in option.** Kubernetes has native ValidatingAdmissionPolicy using CEL (GA since 1.30), evaluated in-process by the API server, and MutatingAdmissionPolicy for CEL-based mutation reached GA in 1.36. No webhook to keep highly available, and therefore no fail-closed outage mode - which is a meaningful reliability advantage. For validation expressible in CEL, this is now the lowest-risk choice, and a sensible architecture uses it for the simple universal rules and a full engine for generation, image verification, lookups, reporting, and exceptions. The engines have converged on this: Kyverno can auto-generate a native VAP from a `ValidatingPolicy`, and Gatekeeper can generate one from a ConstraintTemplate written for its `K8sNativeValidation` (CEL) engine, so the rule runs in-process while the engine keeps its audit and reporting. See [when ValidatingAdmissionPolicy replaces a policy engine](./what-is-validatingadmissionpolicy-and-when-does-it-replace-a-policy-engine.md).

**Whichever you pick, the operational concerns are identical:** the webhook's failure policy and its blast radius, narrow match rules so you are not in the path of every API call, exclusion of your own namespaces, audit-before-enforce rollout, tests with fixtures, and policies delivered as a versioned bundle to every cluster.

**Running both engines is the mistake.** Two policy languages, two upgrade treadmills, and no single place to answer "what rules apply to this workload". Pick one engine, plus native CEL policies where they fit.

## Example

```yaml
# The same policy in each. This comparison is what actually decides adoption.

# --- Gatekeeper: a reusable template in Rego, then a constraint ---
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata: { name: k8srequiredlabels }
spec:
  crd:
    spec:
      names: { kind: K8sRequiredLabels }
      validation:
        openAPIV3Schema:
          properties:
            labels: { type: array, items: { type: string } }
  targets:
    - target: admission.k8s.gatekeeper.sh
      code:
        - engine: Rego
          source:
            version: "v1" # opt in to Rego v1 (OPA 1.0 syntax); v0 is the default
            rego: |
              package k8srequiredlabels

              violation contains {"msg": msg} if {
                some required in input.parameters.labels
                not input.review.object.metadata.labels[required]
                msg := sprintf("missing required label: %v", [required])
              }
---
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sRequiredLabels
metadata: { name: must-have-owner }
spec:
  match: { kinds: [{ apiGroups: ["apps"], kinds: ["Deployment"] }] }
  parameters: { labels: ["platform.example.com/owner"] }
```

```yaml
# --- Kyverno: one resource, CEL logic (policies.kyverno.io/v1, Kyverno 1.17+) ---
apiVersion: policies.kyverno.io/v1
kind: ValidatingPolicy
metadata: { name: must-have-owner }
spec:
  validationActions: [Deny]
  matchConstraints:
    resourceRules:
      - apiGroups: ["apps"]
        apiVersions: ["v1"]
        operations: ["CREATE", "UPDATE"]
        resources: ["deployments"]
  validations:
    - expression: "'platform.example.com/owner' in object.metadata.?labels.orValue({})"
      message: "missing required label platform.example.com/owner"
```

```yaml
# Kyverno's differentiator - generation. A new tenant namespace automatically
# gets its baseline isolation, with no separate controller written.
apiVersion: policies.kyverno.io/v1
kind: GeneratingPolicy
metadata: { name: tenant-namespace-baseline }
spec:
  evaluation:
    synchronize:
      enabled: true # keeps the generated resource in step; restores deletions
  matchConstraints:
    resourceRules:
      - apiGroups: [""]
        apiVersions: ["v1"]
        operations: ["CREATE"]
        resources: ["namespaces"]
  matchConditions:
    - name: is-tenant
      expression: "has(object.metadata.labels) && 'platform.example.com/tenant' in object.metadata.labels"
  variables:
    - name: defaultDeny
      expression: >-
        [{
          "apiVersion": dyn("networking.k8s.io/v1"),
          "kind": dyn("NetworkPolicy"),
          "metadata": dyn({"name": "default-deny-ingress"}),
          "spec": dyn({"podSelector": dyn({}), "policyTypes": dyn(["Ingress"])})
        }]
  generate:
    - expression: generator.Apply(object.metadata.name, variables.defaultDeny)
```

```text
Choosing:

  Do you already run OPA for non-Kubernetes policy (APIs, Terraform, authz)?
    yes -> Gatekeeper. One language across all of it is a genuine benefit.
    no  -> continue

  Do you need mutation and resource generation as first-class capabilities?
    yes -> Kyverno
    no  -> continue

  Is your policy expressible as CEL validation (or, on 1.36+, simple mutation)?
    yes -> native ValidatingAdmissionPolicy / MutatingAdmissionPolicy, or an
           engine policy that generates one. No webhook, no fail-closed risk.
    no  -> continue

  Does your team have Rego expertise, and will it still be here in two years?
    no  -> Kyverno. Maintainability by more than one person beats expressiveness.

  Either way: pick ONE engine, plus native CEL where it fits. Two engines means
  two languages and no single answer to "what applies to this workload".
```

## Interview tips

- Lead with the language difference and its real consequence: whether anyone besides the author can maintain the policy set. That is a more useful framing than a feature comparison.
- Kyverno's mutation and generation as first-class capabilities is the substantive technical differentiator, and generation of namespace baselines is a concrete example worth giving.
- Naming the existing-OPA-investment case as the strongest reason for Gatekeeper shows you decide on context rather than preference.
- Bringing up native ValidatingAdmissionPolicy with CEL (GA 1.30, with MutatingAdmissionPolicy GA in 1.36), and its reliability advantage of having no webhook to keep available, is current and high signal.
- Show you are current on both engines: Kyverno's CEL policy types replace `ClusterPolicy` (deprecated in 1.19, removal planned for 1.20), and OPA 1.0 made Rego v1 the default, which Gatekeeper supports as an opt-in per template. The CEL shift also narrows the old "YAML versus Rego" learning-curve argument: the comparison today is closer to CEL versus Rego.
- Note that the operational concerns are identical either way - failure policy, narrow matching, self-exclusion, audit-before-enforce - because that is what actually determines whether a policy engine causes an outage.
- "Pick one engine" is the closing recommendation, and it answers the common follow-up about teams having adopted different tools.

---

[⬅ Back to Policy as Code and Governance](./README.md) · [All topics](../README.md)
