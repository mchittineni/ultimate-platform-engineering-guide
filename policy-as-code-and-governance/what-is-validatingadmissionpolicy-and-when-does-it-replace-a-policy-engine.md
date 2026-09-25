---
title: "What is ValidatingAdmissionPolicy and when does it replace a policy engine?"
id: 142
category: "Policy as Code and Governance"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - policy-as-code-and-governance
  - interview-questions
---

# What is ValidatingAdmissionPolicy and when does it replace a policy engine?

**Short answer:** ValidatingAdmissionPolicy (VAP) is Kubernetes' built-in way to validate objects at admission using CEL expressions, evaluated inside the API server with no webhook. It has been GA since Kubernetes 1.30, and its mutating counterpart, MutatingAdmissionPolicy, reached GA in 1.36. It replaces a policy engine for rules that can be expressed from the object itself, its namespace, and a parameter resource. You still need an engine such as Kyverno or Gatekeeper for resource generation, image signature verification, lookups of other cluster state or external data, and the reporting and exception workflow around policy. Increasingly the engines themselves compile policies down to VAP, so the real question is less "VAP or engine" and more "which rules run in-process".

## Detail

**The mechanism.** A webhook-based engine receives every matching admission request over HTTPS from the API server, evaluates it in its own pods, and replies. VAP moves evaluation into the API server: the policy is a CEL expression that the API server compiles, type-checks against the resource schema, and runs with a bounded cost budget. Nothing leaves the process.

**Why that matters operationally.** Three problems disappear with the webhook:

- **No availability dependency.** A webhook with `failurePolicy: Fail` blocks matching API calls whenever its pods are down, including during a cluster upgrade or a node drain of the engine itself. That is one of the most common self-inflicted platform outages. VAP has no pods to lose.
- **No added latency or network hop** on every matching request.
- **No certificate and webhook configuration to manage** across a fleet.

**The object model separates rule from scope.** A `ValidatingAdmissionPolicy` holds the logic: `matchConstraints` for which resources it can apply to, optional `matchConditions` to skip requests cheaply, `variables` for reusable sub-expressions, and `validations` with a `message` or computed `messageExpression`. A `ValidatingAdmissionPolicyBinding` decides where and how it applies: a namespace or object selector, the `validationActions` (`Deny`, `Warn`, `Audit`), and optionally a `paramRef` pointing to a parameter resource. One policy can have several bindings, for example `Deny` in production namespaces and `Warn` in sandboxes, which is exactly the shape a staged rollout needs.

**What CEL can see.** The incoming `object` and `oldObject`, the `request` (including the user and operation), `params` from the bound parameter resource, `namespaceObject` for the target namespace's labels, and an `authorizer` for checking the requester's permissions. That covers the large majority of platform rules: required labels, security context, resource requests, allowed registries, forbidden host paths, replica limits by namespace tier.

**Where it stops, and an engine is still needed:**

| Need                                           | VAP / MAP                                   | Kyverno or Gatekeeper                     |
| ---------------------------------------------- | ------------------------------------------- | ----------------------------------------- |
| Validate fields of the object                  | Yes                                         | Yes                                       |
| Mutate / add defaults                          | Yes, with MutatingAdmissionPolicy (GA 1.36) | Yes                                       |
| Generate other resources (namespace baselines) | No                                          | Kyverno yes; Gatekeeper no                |
| Verify image signatures and attestations       | No                                          | Kyverno built in; Gatekeeper via provider |
| Look up other cluster objects or external APIs | No (params and namespace only)              | Yes                                       |
| Scan existing resources in the background      | No; `Audit` only sees admissions            | Yes, with reports                         |
| Exceptions workflow, policy reports, CLI tests | Minimal                                     | First-class                               |
| Webhook availability risk                      | None                                        | Present, unless compiled to VAP           |

**The engines now compile to it.** Kyverno's CEL-based `ValidatingPolicy` uses the same expression model as VAP and can automatically generate a native ValidatingAdmissionPolicy and binding when the policy only uses VAP-compatible features, keeping Kyverno's reporting and background scanning around it. Gatekeeper can express a ConstraintTemplate in CEL with its `K8sNativeValidation` engine and generate a VAP and binding from it. In both cases the rule runs in-process at admission, and the engine provides the fleet management, audits, and exceptions a raw VAP lacks.

**When VAP genuinely replaces an engine.** A small platform, or a cluster type where you want minimal moving parts (a management cluster, an edge cluster), whose rules are all validation against the object and its namespace, and where audit of existing resources is covered some other way. Some teams also choose VAP for the small set of "must never fail open" rules, precisely because there is no webhook to be unavailable, and keep an engine for everything else.

**The trade-offs.** CEL is easier than Rego but still a language. Long `all()` and `exists()` chains get hard to read, and they need tests like any policy. Plain VAP has no background scan, so `Audit` alone under-counts violations on resources that never change. A `failurePolicy` still exists and governs what happens when an expression errors or a parameter resource is missing; `Fail` with a missing `paramRef` target will reject every matching request. And VAP only protects the cluster it is installed on, so it needs the same versioned, GitOps-delivered bundle as any other policy.

## Example

```yaml
# A parameterised policy: allowed registries differ by tenant tier, set in a
# ConfigMap the platform manages. admissionregistration.k8s.io/v1 (GA 1.30).
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicy
metadata:
  name: allowed-registries
spec:
  failurePolicy: Fail
  paramKind:
    apiVersion: v1
    kind: ConfigMap
  matchConstraints:
    resourceRules:
      - apiGroups: [""]
        apiVersions: ["v1"]
        operations: ["CREATE", "UPDATE"]
        resources: ["pods"]
  matchConditions:
    # Cheap pre-filter: skip platform components entirely.
    - name: not-platform-namespace
      expression: "!request.namespace.startsWith('platform-')"
  variables:
    - name: allowed
      expression: "params.data['registries'].split(',')"
    - name: images
      expression: >-
        object.spec.containers.map(c, c.image) +
        object.spec.?initContainers.orValue([]).map(c, c.image)
  validations:
    - expression: "variables.images.all(img, variables.allowed.exists(r, img.startsWith(r)))"
      messageExpression: >-
        'Images must come from an approved registry for this tier: ' +
        params.data['registries'] + '. Rebuild through the platform pipeline,
        which publishes to the approved registry automatically.'
      reason: Forbidden
---
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicyBinding
metadata:
  name: allowed-registries-regulated
spec:
  policyName: allowed-registries
  validationActions: [Deny]
  paramRef:
    name: registries-regulated
    namespace: platform-policy
    parameterNotFoundAction: Deny # fail closed if the ConfigMap is missing
  matchResources:
    namespaceSelector:
      matchLabels:
        platform.example.com/tier: regulated
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: registries-regulated
  namespace: platform-policy
data:
  registries: "registry.example.com/prod/"
```

```text
Deciding, rule by rule:

  Can it be decided from the object, its namespace, and a parameter resource?
    no  -> engine (lookups, external data, image signatures, generation)
    yes -> continue
  Does it need to add or change fields?
    yes -> MutatingAdmissionPolicy on 1.36+, or engine mutation on older clusters
  Do you need background audit, reports, and exceptions for it?
    yes -> write it as a Kyverno ValidatingPolicy (or Gatekeeper CEL template)
           and let the engine generate the VAP
    no  -> plain VAP, delivered via GitOps with the rest of the policy bundle
```

## Interview tips

- Lead with the mechanism: CEL evaluated in-process by the API server, so there is no webhook to be down, slow, or misconfigured. The fail-closed outage mode of webhook engines is the thing it removes.
- Know the dates: VAP GA in 1.30, MutatingAdmissionPolicy GA in 1.36. Saying "native policy can mutate now" is current and high signal.
- Explain the policy and binding split, and use it: one policy, `Deny` in production and `Warn` elsewhere.
- List precisely what VAP cannot do: generate resources, verify image signatures, look up arbitrary cluster state or external data, and scan existing resources.
- The senior answer is that it is no longer either/or. Kyverno and Gatekeeper can generate VAPs from CEL policies, so rules run in-process while the engine keeps reports, background scans, and exceptions.
- Mention `failurePolicy` and `parameterNotFoundAction`. Failing closed still exists, just for different reasons.
- Related: [how Gatekeeper and Kyverno differ](./how-do-gatekeeper-and-kyverno-differ-and-how-do-you-choose.md) and [admission control as a platform lever](../kubernetes-platform/what-is-admission-control-and-how-do-you-use-it-as-a-platform-lever.md).

---

[⬅ Back to Policy as Code and Governance](./README.md) · [All topics](../README.md)
