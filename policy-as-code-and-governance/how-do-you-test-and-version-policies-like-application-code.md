---
title: "How do you test and version policies like application code?"
id: 145
category: "Policy as Code and Governance"
difficulty: "Advanced"
tags:
  - platform-engineering
  - policy-as-code-and-governance
  - interview-questions
---

# How do you test and version policies like application code?

**Short answer:** Keep policies in one repository with the same pipeline as a service: lint and format, unit tests with allowed and denied fixtures for every rule, and an impact test that evaluates the new version against a snapshot of real resources and reports what would change. Then release the policy set as a versioned, signed bundle, with semantic versions that mean something (a new enforced rule is a breaking change), and promote it through environments by GitOps with audit mode as the first stage. The point is that a policy is a production change with cluster-wide reach, and it deserves at least the discipline of the services it governs.

## Detail

**Why this matters more than for most code.** A bad service release breaks one service. A bad policy release can reject every deploy in every cluster, or silently stop enforcing a control an auditor relies on. Both failures are common, and both are invisible until a real change hits them. The users here are every application team whose deploys go through the policy, plus the security and compliance teams who rely on the control being there.

**Layer 1: static checks.** Formatting and linting catch whole classes of error before any test runs. For Rego: `opa fmt`, `opa check --strict` (unused variables, shadowing, deprecated built-ins), and the Regal linter. Since OPA 1.0 made Rego v1 the default, `opa check` also catches v0-style policies that no longer parse. For Kubernetes-native policies: schema validation of the manifests, and for CEL, the API server's own type checking (a VAP's `status.typeChecking` reports expressions that reference fields that do not exist).

**Layer 2: unit tests with both outcomes.** Every rule needs at least one fixture that must pass and one that must fail, plus the edge cases that break naive policies: a field that is missing rather than false, an empty list, an init container, a `DELETE` operation, a resource in an excluded namespace. A test suite with only failing fixtures will happily accept a policy that denies everything. Each engine has its own runner:

| Policy type                           | Test runner                       | Fixture format                            |
| ------------------------------------- | --------------------------------- | ----------------------------------------- |
| Rego (OPA, Conftest)                  | `opa test`, `conftest verify`     | Rego test rules using `with input as`     |
| Gatekeeper ConstraintTemplates        | `gator verify`                    | `Suite` manifest plus sample objects      |
| Kyverno (legacy and CEL policy types) | `kyverno test`                    | `Test` manifest plus resources            |
| Native ValidatingAdmissionPolicy      | `kyverno test`, or a test cluster | `Test` with `isValidatingAdmissionPolicy` |

Measure coverage where the tool supports it (`opa test --coverage`). Uncovered lines in a policy are branches nobody has proved behave as intended.

**Layer 3: impact analysis against real resources.** Unit tests prove the policy does what you meant. They do not tell you what it will do to the estate. For that, export the current resources (or a recent Terraform plan corpus) and run both the current and the proposed policy version against them in CI, then post the difference on the pull request: "this change newly denies 14 resources in 6 namespaces; here is the list". Kyverno's `kyverno apply` can evaluate against a live cluster, and `gator` and `opa eval` work on exported files. This is the test that turns "we think this is safe" into a number, and it is the one most teams are missing.

**Versioning: make the version number carry risk.** Treat the policy set as a released artefact with semantic versions defined by their effect on users, not on the code:

- **Major**: a new rule in enforce mode, or an existing rule tightened. Something that passed yesterday may now be rejected.
- **Minor**: a new rule in audit or warn mode, or a rule relaxed.
- **Patch**: message, documentation, or refactor with no change in decisions (the impact test must show zero difference).

Every policy should carry metadata that auditors and developers need: an owner, the control it implements, a link to documentation, and the date it was introduced. Rego supports this with `# METADATA` annotations; Kubernetes policies use annotations.

**Release and delivery.** Build the policy set into a single immutable artefact: an OPA bundle (which OPA can pull from an OCI registry and verify against a signature) or a tagged directory of Kubernetes manifests delivered by Argo CD or Flux. Clusters and CI jobs pin a version, so you always know which policy version made a given decision. Decision logs and policy reports should record that version, which is what lets you answer an auditor's "which rules were in force on 3 March?".

**Promotion mirrors a service rollout.** The same version moves dev, then staging, then production, with a soak between. New rules ship in audit or warn first; the version that switches them to enforce is a separate, smaller release. Rollback is re-pinning the previous version, which should be as fast and as normal as rolling back a deployment.

**The trade-offs.** The full pipeline is real work to build and keep current, and impact analysis needs a representative export that itself must be kept fresh and free of secrets. Over-strict semantic versioning can slow urgent security fixes; the usual answer is an expedited path that still runs every test but skips the soak. And tests only cover the cases someone thought of. Audit mode in real environments remains the final test, which is why it is a stage in the pipeline and not an optional extra.

## Example

```rego
# policies/terraform/s3/public_bucket.rego - checked in CI by Conftest against
# `terraform show -json` output. Rego v1 syntax (OPA 1.x default).

# METADATA
# title: S3 buckets must block public access
# custom:
#   control: CTL-014
#   owner: group:platform-security
package terraform.s3

deny contains msg if {
  some rc in input.resource_changes
  rc.type == "aws_s3_bucket_public_access_block"
  some action in rc.change.actions
  action in {"create", "update"}
  some setting in ["block_public_acls", "block_public_policy", "ignore_public_acls", "restrict_public_buckets"]
  # object.get, not rc.change.after[setting]: a MISSING setting must fail too.
  # The first version of this rule used direct indexing, and the
  # missing-setting test below caught that it silently passed.
  object.get(rc.change.after, setting, false) != true
  msg := sprintf("%s: %s must be true. Public buckets are not allowed; use the platform CDN module to serve public content.", [rc.address, setting])
}
```

```rego
# policies/terraform/s3/public_bucket_test.rego - both outcomes, plus edge cases.
package terraform.s3_test

import data.terraform.s3

block(after) := {"resource_changes": [{
  "address": "aws_s3_bucket_public_access_block.assets",
  "type": "aws_s3_bucket_public_access_block",
  "change": {"actions": ["create"], "after": after},
}]}

all_true := {
  "block_public_acls": true,
  "block_public_policy": true,
  "ignore_public_acls": true,
  "restrict_public_buckets": true,
}

test_fully_blocked_bucket_is_allowed if {
  count(s3.deny) == 0 with input as block(all_true)
}

test_public_policy_is_denied if {
  msgs := s3.deny with input as block(object.union(all_true, {"block_public_policy": false}))
  count(msgs) == 1
  some m in msgs
  contains(m, "block_public_policy must be true")
}

test_missing_setting_is_denied if {
  count(s3.deny) == 1 with input as block(object.remove(all_true, ["ignore_public_acls"]))
}

test_deleted_block_is_not_evaluated_here if {
  count(s3.deny) == 0 with input as {"resource_changes": [{
    "address": "aws_s3_bucket_public_access_block.old",
    "type": "aws_s3_bucket_public_access_block",
    "change": {"actions": ["delete"], "after": null},
  }]}
}
```

```yaml
# policies/kubernetes/tests/require-owner-label/kyverno-test.yaml
# The same discipline for a Kyverno CEL ValidatingPolicy.
apiVersion: cli.kyverno.io/v1alpha1
kind: Test
metadata:
  name: require-owner-label
policies: [../../require-owner-label.yaml]
resources: [resources.yaml]
results:
  - isValidatingPolicy: true
    policy: require-owner-label
    kind: Deployment
    resources: [checkout] # valid group:team-* owner
    result: pass
  - isValidatingPolicy: true
    policy: require-owner-label
    kind: Deployment
    resources: [no-owner, malformed-owner] # missing; "payments" without group:team-
    result: fail
```

```text
The pipeline on every pull request to the policy repository:

  $ make policy-ci
  fmt      opa fmt --fail .                          ok
  lint     opa check --strict . && regal lint .      ok
  unit     opa test . --coverage                     PASS 4/4, coverage 100%
           kyverno test policies/kubernetes/tests    PASS 23/23
  impact   evaluate v4.2.0 and this branch against last night's export
             resources evaluated ............ 3,184
             newly denied ...................    14   (6 namespaces, list attached)
             newly allowed ..................     0
             decision unchanged ............. 3,170
  version  change classification: new ENFORCED rule -> MAJOR -> v5.0.0
           (the bot suggests: ship as v4.3.0 in Audit first, enforce in v5.0.0)

On merge:  build bundle, sign it, push policy-bundle:4.3.0; Argo CD promotes
           dev -> staging -> prod with a soak; decision logs record 4.3.0.
Rollback:  re-pin 4.2.0. Same path, same speed as any deployment rollback.
```

## Interview tips

- Open with why it matters: a policy is a production change with cluster-wide reach, and a policy that denies everything and one that allows everything both pass a careless test suite.
- Name the three layers: static checks, unit tests with allowed and denied fixtures, and impact analysis against real resources. The impact test is the one most candidates miss and the one that makes rollouts predictable.
- Give concrete edge cases, especially a missing field versus a false one. The Rego `object.get` fix above is exactly the kind of bug unit tests exist to catch.
- Know the runner per engine: `opa test` and Conftest for Rego, `gator verify` for Gatekeeper, `kyverno test` for Kyverno (including CEL policy types and native VAPs).
- Define semantic versions by effect on users: a new enforced rule is a major change. Ship it in audit first as a minor release.
- Pin versions everywhere and record them in decision logs, so you can say which rules were in force on any date. That links testing to the [audit trail](./what-audit-trail-does-a-platform-owe-its-auditors.md) and to [staged rollout](./how-do-you-roll-out-a-new-policy-without-breaking-every-team.md).

---

[⬅ Back to Policy as Code and Governance](./README.md) · [All topics](../README.md)
