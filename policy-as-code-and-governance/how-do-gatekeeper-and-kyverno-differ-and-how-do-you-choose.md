---
title: "How do Gatekeeper and Kyverno differ, and how do you choose?"
id: 75
category: "Policy as Code and Governance"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - policy-as-code-and-governance
  - interview-questions
---

# How do Gatekeeper and Kyverno differ, and how do you choose?

**Short answer:** Gatekeeper is OPA's Kubernetes integration and expresses policy in Rego, a general-purpose policy language that is powerful and has a real learning curve. Kyverno expresses policy as Kubernetes resources in YAML, which is far more approachable and also generates and mutates resources, not just validates them. For Kubernetes-only policy most teams should pick Kyverno; choose Gatekeeper when you need Rego's expressiveness or already use OPA for policy beyond Kubernetes.

## Detail

**The fundamental difference is the language, and it drives adoption.** Rego is a declarative query language for policy - genuinely powerful, capable of complex logic and cross-resource reasoning, and unfamiliar to almost everyone. Kyverno policies are YAML resources that look like the Kubernetes objects they constrain, so a platform engineer can read and write one immediately. In practice the language determines whether anyone other than the policy author can maintain the policy set, which matters more than raw expressiveness for most estates.

**Kyverno does more than validate.** It validates, mutates, and generates. Mutation is what lets you implement guardrails rather than gates - injecting a security context or a default rather than rejecting the workload. Generation creates resources in response to others, for example producing a default network policy and a resource quota whenever a namespace appears. Gatekeeper's focus is validation, with mutation available but less central.

| Dimension               | Gatekeeper (OPA)             | Kyverno                        |
| ----------------------- | ---------------------------- | ------------------------------ |
| Language                | Rego                         | YAML, Kubernetes-native        |
| Learning curve          | Steep                        | Shallow                        |
| Validate                | Yes                          | Yes                            |
| Mutate                  | Yes, secondary               | Yes, first-class               |
| Generate resources      | No                           | Yes                            |
| Image verification      | Via external data / custom   | Built-in, including provenance |
| Cross-resource logic    | Strong                       | More limited, improving        |
| Beyond Kubernetes       | Yes - OPA is general purpose | Kubernetes-focused             |
| Audit of existing state | Yes                          | Yes                            |
| Testing tooling         | Rego unit tests, mature      | `kyverno test` with fixtures   |

**Where Gatekeeper is genuinely the better answer.** If you already run OPA for API authorisation, Terraform policy, or service-level decisions, using one policy language across all of them is a real benefit - the skills, tests, and libraries transfer. Rego also handles complex logic and reasoning across multiple resources more comfortably. And if your policies need external data, OPA's model for that is more established.

**Where Kyverno wins.** Kubernetes-only estates, teams without Rego expertise, and any case where you want mutation and generation as first-class tools. Built-in image signature and provenance verification is a notable practical advantage, because supply-chain admission verification is one of the highest-value policies a platform runs and having it built in is much simpler than assembling it.

**Do not forget the built-in option.** Kubernetes has native Validating Admission Policy using CEL, evaluated in-process by the API server. No webhook to keep highly available, and therefore no fail-closed outage mode - which is a meaningful reliability advantage. For validation expressible in CEL, this is now the lowest-risk choice, and a sensible architecture uses it for the simple universal rules and a full engine for mutation, generation, and image verification.

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
      rego: |
        package k8srequiredlabels
        violation[{"msg": msg}] {
          required := input.parameters.labels[_]
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
# --- Kyverno: one resource, no new language ---
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata: { name: must-have-owner }
spec:
  validationFailureAction: Enforce
  rules:
    - name: owner-label
      match:
        any: [{ resources: { kinds: [Deployment] } }]
      validate:
        message: "missing required label platform.example.com/owner"
        pattern:
          metadata: { labels: { platform.example.com/owner: "?*" } }
```

```yaml
# Kyverno's differentiator - generation. A new tenant namespace automatically
# gets its baseline isolation, with no separate controller written.
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata: { name: tenant-namespace-baseline }
spec:
  rules:
    - name: default-deny-and-quota
      match:
        any: [{ resources: { kinds: [Namespace], selector: { matchLabels: { "platform.example.com/tenant": "?*" } } } }]
      generate:
        synchronize: true # keeps the generated resource in step; restores deletions
        apiVersion: networking.k8s.io/v1
        kind: NetworkPolicy
        name: default-deny-ingress
        namespace: "{{request.object.metadata.name}}"
        data:
          spec:
            podSelector: {}
            policyTypes: [Ingress]
```

```text
Choosing:

  Do you already run OPA for non-Kubernetes policy (APIs, Terraform, authz)?
    yes -> Gatekeeper. One language across all of it is a genuine benefit.
    no  -> continue

  Do you need mutation and resource generation as first-class capabilities?
    yes -> Kyverno
    no  -> continue

  Is your policy expressible as CEL validation only?
    yes -> native ValidatingAdmissionPolicy. No webhook, no fail-closed risk.
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
- Bringing up native Validating Admission Policy with CEL, and its reliability advantage of having no webhook to keep available, is current and high signal.
- Note that the operational concerns are identical either way - failure policy, narrow matching, self-exclusion, audit-before-enforce - because that is what actually determines whether a policy engine causes an outage.
- "Pick one engine" is the closing recommendation, and it answers the common follow-up about teams having adopted different tools.

---

[⬅ Back to Policy as Code and Governance](./README.md) · [All topics](../README.md)
