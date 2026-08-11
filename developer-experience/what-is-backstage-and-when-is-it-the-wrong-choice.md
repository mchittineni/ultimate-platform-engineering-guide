---
title: "What is Backstage and when is it the wrong choice?"
id: 12
category: "Developer Experience"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - developer-experience
  - interview-questions
---

# What is Backstage and when is it the wrong choice?

**Short answer:** Backstage is an open-source framework, originally from Spotify and now a CNCF project, for building a developer portal - a software catalogue, scaffolding templates, technical documentation, and a plugin system that surfaces your other tools in one place. It is the wrong choice when you have no provisioning behind it, when you cannot staff a frontend application as a long-lived internal product, or when the actual problem is that developers do not have a paved road rather than that they cannot find things.

## Detail

**What it actually gives you.** Four things, of unequal value: the software catalogue (the most valuable part, and the reason most adoptions succeed), software templates for scaffolding new repositories, TechDocs for documentation rendered from Markdown in the service repository, and a plugin ecosystem that pulls in CI status, cloud cost, Kubernetes state, and similar views.

**What it does not give you.** Backstage provisions nothing on its own. It is a presentation and cataloguing layer; the platform capabilities behind it - the pipeline, the reconciler, the infrastructure control plane - are yours to build or buy. Organisations that install Backstage expecting a platform get a well-designed index of the tooling they already had.

**The honest cost.** Backstage is a TypeScript application you fork and own. That means a real frontend and Node.js codebase, an upgrade treadmill against a fast-moving upstream, integration work per plugin, and authentication and authorisation wiring into your identity provider. Teams routinely underestimate this. Budget a meaningful ongoing share of an engineer's time indefinitely, not a one-off installation project.

**When it is the right choice:**

- You have enough services that discovery is a real problem - people genuinely cannot find who owns what.
- You already have provisioning automation and need a front door for it.
- You want scorecards, ownership visibility, and documentation in one place.
- You can staff it as a product with a named owner.

**When it is the wrong choice:**

- **Nothing behind it.** Build the golden path first. A portal over a ticket queue is a nicer form for the same wait.
- **Too few services.** With twenty services in one repository organisation, GitHub search is your catalogue.
- **No frontend capacity.** A half-maintained portal that is stale and occasionally broken erodes trust in the whole platform.
- **The real problem is elsewhere.** If deployments are slow and flaky, a portal does not help and will consume the quarter that should have fixed them.

**The alternatives worth naming.** A generated static catalogue from repository descriptors gets you most of the ownership value for a fraction of the cost. Commercial internal-developer-portal products trade flexibility for not owning a codebase. And Git plus a CLI remains a perfectly respectable developer control plane - many strong platforms have no portal at all, because the portal is the discovery surface, not the platform.

**The sequencing that works.** Catalogue first, from descriptor files. Then documentation. Then scorecards. Then templates. Then plugins, only where a specific question is being asked repeatedly. Teams that start with plugins build a dashboard nobody opens twice.

## Example

```text
Decision path, in the order these questions should be asked:

  Do developers have a working self-service path to production?
      no  -> build that first. Backstage will not fix it, and it will look like
             progress while the actual problem persists.
      yes -> continue

  Can people reliably answer "who owns this service" and "where is its runbook"?
      yes -> you may not need a portal at all. Git + CLI + generated catalogue
             is a legitimate end state.
      no  -> continue

  How many services, and how many teams?
      <25 services -> generate a static catalogue page from repo descriptors.
                      Cheap, no application to run, solves 80% of the problem.
      25+          -> continue

  Can you fund an owner for a TypeScript app, indefinitely?
      no  -> commercial IDP product, or the static catalogue above.
      yes -> Backstage is a reasonable choice.

Then adopt in this order, and stop when the value flattens:
  1. Catalogue (ownership, tier, dependencies)   <- the payload
  2. TechDocs (docs from the service repo)
  3. Scorecards (tier-1 has an SLO, an owner, a runbook)
  4. Software templates (scaffolding for golden paths)
  5. Plugins - only for a question people ask repeatedly
```

## Interview tips

- The line to land: Backstage is a portal framework, not a platform. It presents capabilities; it does not create them.
- Say the cost out loud - a forked TypeScript application with an upgrade treadmill and a permanent owner. Candidates who describe it as free open source have not run it.
- Ranking the catalogue as the most valuable component, and plugins as the least, matches what practitioners find and signals real experience.
- Be ready to say a platform can be excellent with no portal at all. That confidence is a differentiator, since portals are often assumed to be the goal.
- Expect "we installed Backstage and adoption is low" - the answer is almost always that there is no provisioning behind it, or the catalogue is curated rather than generated and has gone stale.

---

[⬅ Back to Developer Experience](./README.md) · [All topics](../README.md)
