---
title: "What is a developer portal and how does it differ from the platform?"
id: 15
category: "Developer Experience"
difficulty: "Beginner"
tags:
  - platform-engineering
  - developer-experience
  - interview-questions
---

# What is a developer portal and how does it differ from the platform?

**Short answer:** A developer portal is the front door to an internal platform. It is a web interface, and increasingly an API that AI agents can call, where developers find services and their owners, read documentation, start software templates, and see the state of what they run. The platform is the set of capabilities behind that door: pipelines, infrastructure provisioning, runtime clusters, secrets, observability, and the control planes that reconcile them. The portal shows capabilities and triggers them. The platform actually delivers them. A portal with nothing behind it is a nicer form for filling in the same ticket.

## Detail

**Who uses it and what it saves them.** The users are product engineers, and increasingly their AI coding assistants. Without a portal, a developer who wants to know "who owns the pricing service, where are its dashboards, and how do I create a new service like it?" has to search chat history, ask around, and copy an old repository. A portal answers those three questions in one place. What it saves is search time and interruptions to other people, not provisioning time. Provisioning time is only saved if the platform behind it is automated.

**What a portal typically contains:**

| Portal feature         | What it does                                                        | Which platform capability it depends on        |
| ---------------------- | ------------------------------------------------------------------- | ---------------------------------------------- |
| Software catalogue     | Lists every service, owner, tier, and dependency                    | Descriptor files and a reconciliation job      |
| Software templates     | Creates a new repository or resource from a golden path             | Pipelines, repo automation, infra provisioning |
| Documentation          | Renders docs from each service repository in one searchable site    | A docs build pipeline (docs-as-code)           |
| Scorecards             | Shows each owner where their services fall short of the standard    | The catalogue plus data from other systems     |
| Plugins and dashboards | Surfaces CI status, deploys, cost, and Kubernetes state per service | The underlying CI, CD, cost, and cluster APIs  |

Every row has something in the right-hand column. That is the whole point of the question: the portal is the presentation layer, and the right-hand column is the platform.

**The layering, stated plainly.** Think of three layers. At the bottom are the resources: clusters, databases, queues, cloud accounts. In the middle is the platform: the APIs, controllers, pipelines, and policy that turn a request into running resources safely and repeatably. On top are the interfaces that developers use to reach the platform: the portal, a CLI, Git (a pull request that changes a spec file), and now MCP servers that expose platform actions to AI agents. The portal is one interface among several. Many good platforms let developers do everything through Git and a CLI and use the portal mainly for discovery.

**Why the distinction matters.** The most common failure in platform programmes is building the portal first. It is visible, it demos well, and it looks like progress. But if the "Create database" button opens a ticket that a human handles three days later, developers have gained nothing except a prettier queue, and they learn quickly that the portal is decoration. The opposite order works: automate a capability first, expose it through Git or a CLI, and add a portal entry for it once it works.

**Build or buy.** Backstage, an open-source CNCF project that started at Spotify, is the most common framework for building a portal. It is flexible but it is an application you own, upgrade, and staff. Commercial internal developer portal products trade that flexibility for not running the codebase yourself. A static catalogue page generated from repository descriptors is a legitimate starting point for smaller organisations. See [What is Backstage and when is it the wrong choice?](./what-is-backstage-and-when-is-it-the-wrong-choice.md) for the trade-offs in detail.

**The trade-off.** A portal adds a single place to look, which reduces cognitive load. It also adds a system that must stay accurate. A portal whose catalogue is out of date is worse than no portal, because people trust it once, get the wrong owner, and stop using it. The portal's accuracy depends on the data being generated automatically from the platform, not typed in by hand.

## Example

```text
One developer request - "I need a new service with a Postgres database" -
traced through the layers. The portal is only the first box.

  INTERFACE (how the developer asks)
    portal: "Create service" template form      <- or CLI, or a PR, or an AI agent via MCP
        |
        v
  PLATFORM (what actually does the work)
    1. scaffolder creates repo from golden-path template
    2. CI pipeline registered automatically
    3. service spec committed:  dependencies: [ postgres: { size: small } ]
    4. control plane (e.g. Crossplane or Terraform automation) provisions Postgres,
       writes credentials to the secret store
    5. GitOps controller deploys the service to the dev cluster
    6. catalogue entry, dashboards, and alert routing created from the spec
        |
        v
  RESOURCES
    repository, pipeline, database, namespace, dashboards

  Remove the portal:    steps 1-6 still work through the CLI or a PR. Slightly less
                        convenient; nothing breaks.
  Remove the platform:  the portal form produces a ticket. Nothing is delivered.
```

## Interview tips

- The line to land: the portal is an interface to the platform, not the platform itself. It presents and triggers capabilities; it does not create them.
- Name the other interfaces (CLI, Git, and MCP servers for AI agents) to show you see the portal as one option among several.
- Say that the right order is capability first, portal second. Interviewers often ask "where would you start?" and "build the portal" is the weak answer.
- Mention that the catalogue must be generated, not curated, or the portal loses trust. It links this question to [service catalogues](./what-is-a-service-catalogue-and-why-does-a-platform-need-one.md).
- If asked about Backstage, call it a framework for building a portal, and mention the ongoing ownership cost.

---

[⬅ Back to Developer Experience](./README.md) · [All topics](../README.md)
