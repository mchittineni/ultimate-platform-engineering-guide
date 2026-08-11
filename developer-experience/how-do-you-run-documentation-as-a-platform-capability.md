---
title: "How do you run documentation as a platform capability?"
id: 15
category: "Developer Experience"
difficulty: "Beginner"
tags:
  - platform-engineering
  - developer-experience
  - interview-questions
---

# How do you run documentation as a platform capability?

**Short answer:** Treat documentation as docs-as-code: Markdown in the repository next to what it describes, reviewed in the same pull request as the change, built and published automatically, and searchable from one place. For an internal platform, documentation is the primary support interface - every question it fails to answer arrives in your support channel instead, so its quality directly determines your operational load.

## Detail

**Why it is a platform capability rather than a chore.** Support load for a platform scales with adoption. If each new team generates the same fifteen questions, growth becomes painful and the team's time goes to answering rather than building. Documentation is the mechanism that decouples adoption from support cost, which makes it infrastructure.

**Docs-as-code, concretely:** documentation lives in the repository it describes; it is written in Markdown; changing behaviour without updating the docs fails review; a pipeline renders and publishes on merge; and the published site is indexed centrally so people find it without knowing which repository it came from. Backstage's TechDocs is one implementation; a static site generator publishing to one place is another and is entirely adequate.

**Wiki pages fail predictably.** A wiki is a separate system with no relationship to the code, so it drifts immediately, has no review gate, accumulates duplicates that disagree, and gives no signal about which page is current. The characteristic symptom is three pages describing three different deployment procedures, all of which were true once.

**The types of documentation are not interchangeable.** The Diátaxis framework is worth naming because conflating these is the most common quality failure:

| Type        | Answers                               | Platform example                         |
| ----------- | ------------------------------------- | ---------------------------------------- |
| Tutorial    | How do I learn this?                  | "Deploy your first service" - end to end |
| How-to      | How do I do this specific task?       | "Add a Postgres database to a service"   |
| Reference   | What are the exact fields and values? | Every field of the service specification |
| Explanation | Why is it like this?                  | "Why the platform owns base images"      |

A reference table cannot teach a newcomer, and a tutorial cannot answer a precise question at 3am. Most platform documentation is all how-to and no explanation, which is why teams follow instructions without understanding and cannot adapt when something is unusual.

**Generate what can be generated.** The reference documentation for a platform API should come from the schema - the custom resource definition, the JSON Schema, the module variables - so it cannot drift. Hand-written reference documentation for a machine-readable interface is guaranteed to be wrong eventually.

**Close the loop with evidence.** Instrument search terms that return nothing, pages with high exit rates, and the questions actually asked in your support channel. Every recurring question is a documentation defect; the standard practice worth adopting is that answering a support question in chat is not finished until the answer exists in the docs and the asker was pointed at it.

## Example

```text
Repository layout - docs live with the thing they describe:

  checkout/
    docs/
      index.md              explanation: what this service is and why it exists
      runbook.md            how-to: the incident procedures, linked from alerts
      api.md                reference: generated from the OpenAPI spec
    mkdocs.yml
    .platform/catalog-info.yaml   -> annotation points the portal at docs/

Platform-owned documentation, structured by type rather than by tool:

  platform-docs/
    tutorials/first-service.md          30 minutes, works start to finish
    how-to/add-a-database.md            one task, no theory
    how-to/roll-back-a-deploy.md
    reference/service-spec.md           GENERATED from the CRD schema
    reference/policies.md               GENERATED from the policy bundle
    explanation/why-we-own-base-images.md
    explanation/tenancy-model.md
```

```yaml
# The gate that keeps documentation honest: a behaviour change without a docs
# change is a review conversation, not a silent merge.
- name: Docs touched when the platform interface changes
  on: pull_request
  if: changed('api/v1/**') && !changed('docs/reference/**')
  action: request-review
  message: >
    This changes the platform API but no reference documentation changed.
    If the reference is generated, regenerate it; if this is genuinely
    internal-only, say so in the PR and this check can be waived.
```

## Interview tips

- The framing that earns credit: documentation is the platform's support interface, and its quality determines whether support load scales with adoption.
- Say docs-as-code and give the specifics - same repository, same pull request, published automatically. "We should write more docs" is not an answer.
- Naming Diátaxis and the four types, especially the missing-explanation problem, distinguishes this from a generic answer.
- "Generate reference documentation from the schema" is concrete and shows you have dealt with drift.
- The support-channel rule - an answer is not finished until it is in the docs - is a practice interviewers recognise from teams that got this right.

---

[⬅ Back to Developer Experience](./README.md) · [All topics](../README.md)
