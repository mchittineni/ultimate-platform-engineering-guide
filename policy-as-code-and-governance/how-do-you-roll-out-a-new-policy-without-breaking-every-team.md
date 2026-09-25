---
title: "How do you roll out a new policy without breaking every team?"
id: 143
category: "Policy as Code and Governance"
difficulty: "Advanced"
tags:
  - platform-engineering
  - policy-as-code-and-governance
  - interview-questions
---

# How do you roll out a new policy without breaking every team?

**Short answer:** Run it in audit mode first and count the violations, fix as many as you can yourself through mutation or automated pull requests, grandfather what remains with an expiry, apply enforcement to new resources before existing ones, and only then enforce everywhere. The failure to avoid is enabling enforcement on day one and rejecting a third of the estate's next deploy - which costs you the credibility you need for every subsequent policy.

## Detail

**Measure before you enforce.** The first question is how many resources violate the policy today, and the answer is frequently much larger than expected. Audit mode evaluates without rejecting and gives you that number plus the specific list, which converts the rollout from a hope into a plan with known work in it. Admission-time audit only sees changes, so pair it with a background scan of existing resources to get the full count. See [audit mode versus enforce mode](./what-is-the-difference-between-audit-mode-and-enforce-mode-for-a-policy.md).

**Fix what you can without asking anyone.** For a large share of policies the violation is mechanical - a missing label, an absent resource request, no security context - and the platform can either mutate the resource at admission or raise the pull request itself. Doing this first collapses the violation count and means enforcement, when it arrives, affects very few teams. The ratio of violations you fix to violations you assign is what determines how the rollout is received.

**Grandfather deliberately, with expiry.** Whatever remains after automated fixing needs an exemption with an owner and a date. Grandfathering without an expiry means the policy is permanently not enforced for the resources that most needed it; grandfathering with an expiry converts a blocker into a scheduled conversation.

**Enforce for new resources before existing ones.** Applying the policy on create, while existing resources are still exempt, stops the problem growing while you work through the backlog. It also gives you a period where the policy's error messages are being exercised by real users, which is when you discover they are unclear.

**Use warn as the step between audit and enforce.** Native ValidatingAdmissionPolicy bindings and Kyverno's CEL policies accept `validationActions: [Warn, Audit]` (Gatekeeper uses `enforcementAction: warn`): the change succeeds, but the developer sees the violation in their own `kubectl` or pipeline output. It is per-team communication that costs nothing to send.

**Wave the rollout the way you would any fleet change.** Dev, then staging, then low-tier production, then everything - with a soak between waves. Each wave surfaces a different class of violation, and the earlier waves are where you find that your policy has a false positive.

**Communicate specifically, per team, with the fix attached.** "We are enforcing resource requests next month" produces nothing. "Your service `reporting-api` has no memory request; here is pull request #482 which adds it; this becomes enforced on 15 January" produces action. Aggregate announcements are for awareness; per-team specifics are for change.

**Have an abort condition.** If enforcement starts rejecting things you did not predict, you need a fast way back to audit mode, and it should be as easy as any other rollback. A policy rollout is a production change with cluster-wide reach.

**Watch for the false positives in the tail.** The last few violations are often not laziness but a legitimate case your policy did not anticipate - a workload that genuinely needs a privileged capability, a system component that cannot carry your label scheme. Treating those as policy bugs rather than team failures is both correct and how you keep the relationship.

## Example

```text
Rolling out "every container must set CPU and memory requests" across 218
workloads. The point of the whole sequence is that only 11 teams ever see a
failure they have to act on themselves.

WEEK 1 - MEASURE (audit mode, all clusters, enforcement off)
  workloads evaluated ................ 218
  violations ......................... 147   <-- two thirds of the estate
    missing both requests ............  63
    missing memory only ..............  71
    missing cpu only .................  13
  If enforcement had been enabled on day one, 147 teams' next deploy fails.

WEEK 2 - FIX WITHOUT ASKING (mutation + automated PRs)
  mutating policy injects LimitRange defaults where absent .... 147 -> 38
  automated PRs raised for the 38 where a default is wrong
    (memory-heavy workloads that would OOM at 128Mi) ......... 38 PRs
  27 merged within the week ................................... 38 -> 11
  violation count now 11. This is the ratio that matters: 136 of 147 fixed by
  the platform, 11 assigned to teams.

WEEK 3 - GRANDFATHER THE REMAINDER, WITH EXPIRY
  11 exemptions created, each with an owner and a date:
      6 x waiting on team capacity          expires 2027-01-15
      3 x genuinely need higher limits,
          budget approval in progress       expires 2027-01-29
      2 x FALSE POSITIVES - system DaemonSets that cannot carry requests
          in the way the policy expects     -> POLICY BUG. Match rules
                                               narrowed to exclude kube-system.
                                               Not the teams' problem.

WEEK 4 - ENFORCE FOR NEW RESOURCES ONLY
  create -> enforced. update of an existing resource -> audit.
  New violations become impossible; the backlog does not grow. Error messages
  get exercised by real users - two were rewritten after confusing people.

WEEK 5-7 - WAVE ENFORCEMENT FOR EXISTING RESOURCES
  dev (soak 3d) -> staging (3d) -> prod tier 3 (5d) -> prod tier 1-2
  abort condition: any unexpected rejection of a tier-1 workload reverts the
  wave to audit within minutes.

WEEK 8 - ENFORCED EVERYWHERE
  violations 0, exemptions 9 (all with expiry), policy bug fixed.
  Zero unplanned deploy failures across the whole rollout.
```

```yaml
# Enforce on create; existing resources stay in the background audit. Stops
# growth while the backlog is worked. Kyverno CEL policy type
# (policies.kyverno.io/v1); the legacy ClusterPolicy format is deprecated.
apiVersion: policies.kyverno.io/v1
kind: ValidatingPolicy
metadata:
  name: require-resource-requests
  annotations:
    platform.example.com/rollout-phase: "new-resources-only"
    platform.example.com/enforce-existing-from: "2027-01-15"
spec:
  validationActions: [Deny]
  matchConstraints:
    resourceRules:
      - apiGroups: [""]
        apiVersions: ["v1"]
        # CREATE only: updates to existing workloads are not evaluated yet, and
        # the background scan keeps counting them.
        operations: ["CREATE"]
        resources: ["pods"]
  matchConditions:
    # The narrowed match after the false positives were found in week 3:
    # tenant namespaces only, so kube-system and platform-* are out of scope.
    - name: tenant-namespaces-only
      expression: "request.namespace.startsWith('team-')"
    # Grandfathered resources, by explicit annotation with an expiry that the
    # exemption controller enforces
    - name: not-grandfathered
      expression: >-
        object.metadata.?annotations[?'platform.example.com/policy-exemption']
        .orValue('') != 'require-resource-requests'
  validations:
    - expression: >-
        object.spec.containers.all(c,
          has(c.resources) && has(c.resources.requests) &&
          'cpu' in c.resources.requests && 'memory' in c.resources.requests)
      message: >-
        Container has no cpu/memory request, so it runs as BestEffort and is
        evicted first under node pressure. The platform's LimitRange normally
        supplies defaults - if you are seeing this, your namespace overrides it.
        Set `resources.requests`. See go/platform-resources.
```

## Interview tips

- Lead with "measure first in audit mode" and give a number. The fact that two thirds of the estate violates a reasonable policy is the insight that justifies the whole sequence.
- The fix-it-yourself ratio is the strongest point: 136 of 147 fixed by the platform, 11 assigned to teams. That is what determines whether the rollout builds or destroys credibility.
- Enforce on create before enforcing on update is a specific, clever step that stops the backlog growing while you work it, and most candidates do not mention it.
- Grandfathering must have expiry dates, or the resources that most needed the policy are permanently exempt.
- Treating the last few violations as probable policy bugs rather than team failures is the senior instinct, and the system DaemonSet example makes it concrete.
- Mention warn as the step between audit and enforce: it tells each developer directly at apply time without blocking them.
- Mention an abort condition and a fast route back to audit mode. A policy rollout is a cluster-wide production change and deserves the same rollback thinking.

---

[⬅ Back to Policy as Code and Governance](./README.md) · [All topics](../README.md)
