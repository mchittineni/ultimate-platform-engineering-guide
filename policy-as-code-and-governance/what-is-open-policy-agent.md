---
title: "What is Open Policy Agent?"
id: 134
category: "Policy as Code and Governance"
difficulty: "Beginner"
tags:
  - platform-engineering
  - policy-as-code-and-governance
  - interview-questions
---

# What is Open Policy Agent?

**Short answer:** Open Policy Agent (OPA) is a general-purpose policy engine, a graduated CNCF project, that separates the decision "is this allowed?" from the software that has to enforce it. The caller sends OPA a JSON document describing the request, OPA evaluates it against policies written in a language called Rego plus any reference data it has loaded, and returns a JSON decision. Because the input can be anything, the same engine and language can govern Kubernetes admission, Terraform plans, API authorisation, and CI pipelines.

## Detail

**The core idea is decoupling.** Without a policy engine, rules live as `if` statements scattered through services, scripts, and pipeline YAML, each written differently and none of them easy to audit. OPA moves the rule into one place. The service still enforces the answer (it returns 403, or the admission webhook rejects the object), but it no longer contains the logic. You can change a rule without redeploying the service, test it on its own, and show an auditor every rule in one repository.

**How a decision works.** Three inputs produce one output:

```text
  input (JSON)   - the thing being decided about: an API request, a Kubernetes
                   object, a Terraform plan
  data (JSON)    - reference data OPA has loaded: team ownership, allowed
                   registries, which services are PCI-scoped
  policy (Rego)  - the rules

                   -> OPA evaluates ->   decision (JSON): true/false, a list of
                                         violations, or any structured answer
```

OPA knows nothing about Kubernetes or HTTP. It only sees JSON. That is why it is general purpose, and also why every integration needs a thin layer that turns its domain into JSON input.

**Rego, and what OPA 1.0 changed.** Rego is a declarative query language. You write rules that are true when their conditions hold, and OPA works out the answer; you do not write loops or control flow. OPA 1.0 made the "Rego v1" syntax the default: the `if` keyword is required before a rule body, `contains` is required for rules that build a set, and keywords such as `in`, `some`, and `every` no longer need importing. Older policies written in the v0 style fail to parse on OPA 1.x unless you run it in v0-compatibility mode, so this is the first thing to check when upgrading. Some integrations still default to v0 syntax for compatibility; Gatekeeper, for example, makes Rego v1 opt-in per ConstraintTemplate.

**Where OPA runs.** Usually as close to the caller as possible, because policy decisions are on the request path:

| Integration                  | What it decides                                                    |
| ---------------------------- | ------------------------------------------------------------------ |
| Gatekeeper                   | Kubernetes admission (OPA packaged as an admission webhook)        |
| Conftest                     | Checks config files in CI: Terraform, Kubernetes YAML, Dockerfiles |
| Envoy external authorisation | Per-request API authorisation at the proxy or mesh                 |
| Sidecar or library           | Application authorisation, via REST call or the Go SDK             |

**How policy gets to the engines.** OPA pulls policy and data as signed bundles from an HTTP server or an OCI registry, and can ship decision logs (every input, decision, and policy version) to a central collector. For a platform team that is the attraction: one policy repository, published as a versioned bundle, evaluated by many OPA instances, with an audit trail of every decision.

**Who uses it on a platform.** The platform or security team writes and owns the policies. Application teams meet them indirectly, as a CI failure from Conftest, a rejected `kubectl apply`, or a 403 from the API gateway, which is why the reasons OPA returns matter as much as the yes or no.

**The trade-off.** OPA's generality comes at a cost. Rego is unfamiliar to most engineers, and a policy set only one person can read is a risk. For Kubernetes-only admission rules, Kyverno (policies as Kubernetes resources using CEL) or the built-in ValidatingAdmissionPolicy are often simpler. OPA earns its keep when you want one language across Kubernetes, infrastructure code, and application authorisation.

## Example

```rego
# deploy_authz.rego - who may deploy which service where.
# Rego v1 syntax (the default since OPA 1.0): `if` and `contains` are required.
package platform.deploy

# Default deny: if no rule below matches, the answer is no.
default allow := false

# Anyone on the owning team may deploy to non-production.
allow if {
  input.environment != "production"
  input.user.team == data.services[input.service].owner
}

# Production additionally needs an on-call engineer and a green pipeline.
allow if {
  input.environment == "production"
  input.user.team == data.services[input.service].owner
  "oncall" in input.user.roles
  input.pipeline.status == "passed"
}

# Reasons are part of the decision, so the caller can explain a "no".
reasons contains "production deploys need the oncall role" if {
  input.environment == "production"
  not "oncall" in input.user.roles
}

reasons contains "pipeline has not passed" if {
  input.environment == "production"
  input.pipeline.status != "passed"
}

reasons contains msg if {
  input.user.team != data.services[input.service].owner
  msg := sprintf("%s is owned by %s, not %s", [input.service, data.services[input.service].owner, input.user.team])
}
```

```text
$ cat data.json
{"services": {"checkout": {"owner": "team-payments"}}}

$ cat input.json
{"user": {"name": "alice", "team": "team-payments", "roles": ["developer"]},
 "service": "checkout", "environment": "production",
 "pipeline": {"status": "passed"}}

$ opa eval -d deploy_authz.rego -d data.json -i input.json 'data.platform.deploy' --format pretty
{
  "allow": false,
  "reasons": [
    "production deploys need the oncall role"
  ]
}
```

The same file can be unit tested with `opa test`, published as a bundle, and evaluated by a CI job, a deploy tool, or an OPA sidecar next to the deployment API. Nothing in it knows which of those is calling.

## Interview tips

- Lead with decoupling: OPA makes the decision, the caller enforces it. That one sentence separates people who understand OPA from people who have only heard of it.
- Explain input, data, policy, and decision. Saying "OPA only sees JSON" explains both why it is general purpose and why every integration needs an adapter.
- Mention OPA 1.0 and Rego v1 (`if`, `contains`, no `import rego.v1` needed). It is current, and it is a real upgrade issue for older policy sets.
- Name at least two integrations beyond Kubernetes, such as Conftest for Terraform in CI and Envoy for API authorisation. That is the case for choosing OPA over a Kubernetes-only engine.
- Be honest about Rego's learning curve, and know when Kyverno or ValidatingAdmissionPolicy is the simpler answer. See [how Gatekeeper and Kyverno differ](./how-do-gatekeeper-and-kyverno-differ-and-how-do-you-choose.md).
- A likely follow-up is "how do you test Rego?" The answer is `opa test` with allowed and denied inputs in CI. See [testing and versioning policies](./how-do-you-test-and-version-policies-like-application-code.md).

---

[⬅ Back to Policy as Code and Governance](./README.md) · [All topics](../README.md)
