---
title: "How do you version a platform interface and migrate consumers?"
id: 38
category: "Platform Architecture"
difficulty: "Advanced"
tags:
  - platform-engineering
  - platform-architecture
  - interview-questions
---

# How do you version a platform interface and migrate consumers?

**Short answer:** Version the interface explicitly from the first release, serve old and new versions simultaneously with conversion between them, and migrate consumers yourself with automated pull requests rather than asking teams to do it. The rule that keeps a platform trusted is that a breaking change is your work, not your users' - and the version is only retired when the consumer count reaches zero, verified rather than assumed.

## Detail

**Why this is the highest-stakes design decision.** Your interface is copied into every service repository. Once forty teams have `apiVersion: platform.example.com/v1` committed, you cannot change its meaning. Platform teams that break this contract lose trust in one release and spend a year recovering it, because the rational response for a team burned by a silent breaking change is to stop depending on you.

**Establish what is breaking, and write it down.** Ambiguity here causes most accidental breakage:

| Change                                  | Breaking?                                         |
| --------------------------------------- | ------------------------------------------------- |
| Adding an optional field with a default | No                                                |
| Adding a new enum value                 | No                                                |
| Adding a required field                 | **Yes**                                           |
| Removing or renaming a field            | **Yes**                                           |
| Narrowing validation on existing input  | **Yes**                                           |
| Changing a default's value              | **Yes** - silently changes behaviour              |
| Changing the semantics of a field       | **Yes** - and worst, because it passes validation |

The last two are the dangerous ones: nothing fails, behaviour just changes. Treat a default change as a breaking change and version it.

**Serve multiple versions with conversion.** Kubernetes' pattern is the one to copy: multiple served versions, one storage version, and a conversion path between them. Consumers on the old version keep working unchanged; internally you handle one representation. If you are not on Kubernetes, the same shape applies - accept both, normalise to one, and keep the mapping explicit and tested.

**Migrate for people.** The practice that distinguishes teams that keep trust: write a codemod, run it against every consumer repository, open a pull request per repository with a clear explanation and a link to the diff of what changed and why, and offer to merge it. Batch it - ten repositories at a time, watch for problems, continue. Asking forty teams to each spend an afternoon on your change means half will not, and you support both versions forever.

**Deprecate with a signal, a date, and escalating noise.** Mark the version deprecated in the schema, emit a warning on every use, publish the removal date, and make the warning progressively louder - annotation, then pull-request comment, then a scorecard finding, then a build warning. Never a silent removal, and never a removal without a verified zero-consumer count.

**Verify before you delete.** Query actual usage rather than trusting the migration was complete. Do not remove a version because the deadline passed; remove it because nothing uses it. If three consumers remain, the conversation is with three teams, not an outage.

**When you genuinely cannot migrate someone.** Time-boxed exemptions with a named owner, and the honest cost stated: they keep the old version, they take on the maintenance risk, and there is a review date. Indefinite exemptions are how you end up maintaining v1 for five years.

## Example

```yaml
# Two served versions, one stored, with conversion. Consumers on v1alpha1 keep
# working unchanged while v1 becomes the storage version.
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: services.platform.example.com
spec:
  group: platform.example.com
  names: { kind: Service, plural: services }
  scope: Namespaced
  versions:
    - name: v1alpha1
      served: true # still accepted
      storage: false
      deprecated: true # kubectl prints a warning on every use
      deprecationWarning: >
        platform.example.com/v1alpha1 Service is deprecated; use v1.
        spec.db -> spec.dependencies[].postgres. Removal: 2027-03-01.
        A migration PR has been opened against your repository.
      schema: { openAPIV3Schema: { type: object } } # abbreviated
    - name: v1
      served: true
      storage: true # single internal representation
      schema: { openAPIV3Schema: { type: object } }
  conversion:
    strategy: Webhook # explicit, tested mapping both directions
    webhook:
      clientConfig: { service: { name: platform-conversion, namespace: platform } }
      conversionReviewVersions: ["v1", "v1alpha1"]
```

```text
The migration campaign - what the platform team does, not what it asks for:

  Week 0   v1 ships. v1alpha1 marked deprecated, warning emitted, date published.
           Codemod written and tested against a corpus of real consumer repos.

  Week 1   Migration PRs opened for 8 of 41 repositories (lowest tier first).
             title: "Migrate to platform.example.com/v1 (automated)"
             body:  what changed, why, the exact diff, who to ask, opt-out route
           Two failures found in the codemod. Fixed. This is why you batch.

  Week 2-5 Remaining 33 repos, 10 per batch. Team offers to merge on request.

  Week 6   Verified usage, rather than assumed completion:
             $ platform api-usage --version v1alpha1
               team-legacy/reporting-etl     last applied 3d ago
               team-data/warehouse-sync      last applied 1d ago
           2 consumers remain -> direct conversation, not a deadline email.

  Week 10  $ platform api-usage --version v1alpha1
               (no consumers)
           v1alpha1 `served: false`. Removed from the CRD one release later.

  Elapsed: 10 weeks for 41 consumers, zero broken teams, zero escalations.
  The alternative - "please migrate by March" - reliably leaves a long tail
  that you support indefinitely.
```

## Interview tips

- "A breaking change is my work, not my users' work" is the sentence that wins this question. Automated migration pull requests are the concrete proof.
- Have the breaking-change table ready, and specifically call out that changing a default or a field's semantics is breaking even though nothing fails validation. That detail separates experienced answers.
- Cite the Kubernetes multi-version pattern - served versions, one storage version, conversion webhook - by name; it is the canonical reference and shows you are not inventing a scheme.
- "Retire on verified zero consumers, not on the deadline" is the operational detail interviewers probing for maturity want to hear.
- Expect "what if a team refuses to migrate?" - time-boxed exemption, named owner, stated cost, review date. Never indefinite.

---

[⬅ Back to Platform Architecture](./README.md) · [All topics](../README.md)
