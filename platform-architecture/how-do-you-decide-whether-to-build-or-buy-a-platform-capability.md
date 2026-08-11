---
title: "How do you decide whether to build or buy a platform capability?"
id: 23
category: "Platform Architecture"
difficulty: "Advanced"
tags:
  - platform-engineering
  - platform-architecture
  - interview-questions
---

# How do you decide whether to build or buy a platform capability?

**Short answer:** Build only where the capability is genuinely specific to your organisation and gives you leverage nobody can sell you - typically your own interface, your golden paths, and your glue. Buy or adopt open source for everything that is a solved commodity, which is most of it. The decision is dominated by total cost of ownership rather than build effort, because the build is a one-off and the operating, upgrading, and supporting is forever.

## Detail

**The framing that makes this tractable.** Ask what is differentiating for _your_ organisation. A pipeline, a metrics store, a flag evaluation engine, and a secret manager are commodities - hundreds of organisations need the same thing, and vendors and open-source projects have invested many engineer-years. Your service specification, your golden paths, the mapping from your tiers to your defaults, and the integration between your identity provider and your cloud accounts are specific to you and cannot be bought. Build the second list, buy the first.

**Compare total cost of ownership, not build cost.** The build estimate is the least important number. What matters over three years: initial build, ongoing maintenance, the upgrade treadmill, on-call burden, documentation and support, the opportunity cost of the engineers involved, and the bus factor. A capability built in six weeks that consumes 20% of an engineer indefinitely is expensive.

**Buy is not free either.** Licence cost that scales with your growth, integration effort, vendor lock-in, a roadmap you do not control, data residency and compliance review, procurement time, and the risk of acquisition or discontinuation. Be able to name these, because a candidate who presents buying as costless is not credible.

**Open source in between.** Self-hosting an open-source project is often described as free and is not - you own the operation, the upgrades, and the expertise. But you avoid licensing and lock-in, and can patch. The honest comparison is three-way: build, buy, or adopt-and-operate.

**Signals to buy:** the capability is a commodity; the market is mature with multiple credible options; it is not in your critical request path (or the vendor's reliability genuinely exceeds what you would achieve); you cannot staff it properly; and time to value matters more than fit.

**Signals to build:** it encodes your organisation's specific model; no product fits without contorting your workflow; it is a thin integration between systems you already run; or you have a genuine scale or regulatory constraint that products do not meet. "It would be interesting" and "we could do it better" are not signals - they are the two most common reasons platform teams build things they later regret.

**The strongest pattern: buy the engine, build the interface.** Buy or adopt the flag provider, the metrics backend, the CI runner, the secret store. Build the thin layer that presents them consistently through your platform interface, applies your defaults, and keeps them replaceable. This is where a platform team's leverage genuinely is, and it also preserves your ability to change the engine later.

**Reversibility should shape the decision.** Prefer options you can exit. Wrapping a vendor behind your own interface means switching costs one adapter rather than touching every service. Where an exit is genuinely hard - proprietary query or targeting languages, deeply embedded data models - price that into the decision explicitly.

**Do not skip the "do nothing" option.** Sometimes the honest answer is that the capability is not needed yet, and a documented convention will do until the pain is real.

## Example

```text
A real build/buy/adopt split for one platform, with the reasoning per row.

CAPABILITY                    DECISION   WHY
  Kubernetes                   adopt      commodity; managed offering, no argument
  CI runners                   buy        commodity; hosted, scales, not in request path
  Container registry           buy        commodity; bundled with the cloud provider
  Metrics + traces backend     buy        commodity, but expensive at scale - so we
                                          also build cardinality guardrails in front
  Secret store                 adopt      managed cloud secret manager + CSI driver
  Feature flag engine          buy/adopt  behind an OpenFeature interface, so the
                                          provider is swappable in one adapter
  Policy engine                adopt      Kyverno; commodity, active project
  GitOps reconciler            adopt      Argo CD; commodity, mature
  Developer portal             buy or     depends on frontend capacity; the catalogue
                               generate   data itself is ours either way
  ------------------------------------------------------------------------------
  Service specification (API)  BUILD      encodes our tiers, defaults, and policy.
                                          Nobody can sell us our own opinions.
  Golden path templates        BUILD      our languages, our conventions
  Provisioning compositions    BUILD      our network layout, naming, tagging, IAM
  Catalogue reconciliation     BUILD      thin glue: cluster + cloud + identity
  Tier -> defaults mapping     BUILD      pure organisational policy
  Cost attribution model       BUILD      our team structure and shared-cost rules

  Pattern: every BUILD row is either our interface, our policy, or glue between
  bought pieces. Nothing on that list is an engine.
```

```text
Three-year TCO comparison for one capability, as it should be presented to a
budget holder. The build column loses on the rows that are easy to forget.

  FEATURE FLAG PLATFORM              build ourselves    buy + thin wrapper
    initial engineering              14 wks (2 eng)     2 wks (1 eng)
    licence / subscription           none               scales with usage
    ongoing maintenance              ~15% of 1 eng      ~2% of 1 eng
    on-call surface                  new data-plane     vendor-operated;
                                     dependency         local eval + cached ruleset
    upgrade treadmill                ours forever       vendor's problem
    SDKs to maintain (4 languages)   4                  0 (vendor + OpenFeature)
    audit log, targeting, experiments build all         included
    exit cost                        n/a                one adapter (wrapped)
    opportunity cost                 the golden path we
                                     did not build      -

  Decision: buy the engine, build the wrapper. The wrapper is 2 weeks and is the
  part that keeps the decision reversible.
```

## Interview tips

- "Buy the engine, build the interface" is the sentence to land. It is the correct answer for most platform capabilities and it demonstrates you know where a platform team's leverage actually is.
- Insist on total cost of ownership over three years and name the forgotten rows - maintenance percentage, on-call surface, per-language SDKs, opportunity cost.
- Name the costs of buying too. A candidate who treats buying as free is as unconvincing as one who wants to build everything.
- Call out "it would be interesting" and "we could do it better" as non-signals. Interviewers have usually lived through a platform team that built something on those grounds.
- Volunteer reversibility - wrapping the vendor so an exit costs one adapter - and the "do nothing yet" option. Both are senior moves.

---

[⬅ Back to Platform Architecture](./README.md) · [All topics](../README.md)
