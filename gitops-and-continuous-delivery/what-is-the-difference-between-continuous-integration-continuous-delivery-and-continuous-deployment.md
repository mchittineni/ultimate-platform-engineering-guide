---
title: "What is the difference between continuous integration, continuous delivery, and continuous deployment?"
id: 80
category: "GitOps and Continuous Delivery"
difficulty: "Beginner"
tags:
  - platform-engineering
  - gitops-and-continuous-delivery
  - interview-questions
---

# What is the difference between continuous integration, continuous delivery, and continuous deployment?

**Short answer:** Continuous integration means everyone merges small changes into a shared mainline frequently, and every merge is automatically built and tested. Continuous delivery extends that so every change that passes the pipeline produces an artefact that _could_ be released to production at any moment, with the release itself a deliberate human decision. Continuous deployment removes that final decision: every change that passes the pipeline goes to production automatically. The three are cumulative - you cannot do the later ones without the earlier ones.

## Detail

**Continuous integration is a practice before it is a tool.** The original idea is that developers integrate their work with everyone else's at least daily, so conflicts are small and found early. The automation - a build and test run on every push and pull request - exists to make that frequent integration safe. A team with a CI server but long-lived feature branches merged once a month is not doing continuous integration; it has automated builds and still suffers the "merge hell" CI was invented to prevent. The signals that CI is real: short-lived branches, a mainline that is always green, and fixing a broken build treated as the team's top priority.

**Continuous delivery is about releasability, not release frequency.** The pipeline carries each change past unit tests into packaging, integration tests, security scanning, and deployment to production-like environments. The output is an immutable artefact - usually a container image identified by a digest - with evidence attached that it is fit to ship. Whether you ship it today is a business decision: a release train, a change window, a marketing launch. The defining property is that nothing _technical_ stands between a green pipeline and production.

**Continuous deployment automates the final step.** Every change that passes the pipeline is deployed without anyone pressing a button. This does not mean less safety; it means the safety has moved entirely into automation. It only works when tests are trustworthy, rollouts are progressive (canary or traffic shifting), health checks can abort a bad release, and features that are not ready are hidden behind feature flags rather than held back on a branch.

| Practice               | Every change is...                    | Production release is...           | Main prerequisite                                   |
| ---------------------- | ------------------------------------- | ---------------------------------- | --------------------------------------------------- |
| Continuous integration | Merged to mainline, built, and tested | Not addressed                      | Fast, reliable tests; short-lived branches          |
| Continuous delivery    | Packaged and proven releasable        | A human decision, one click        | Automated pipeline to production-like environments  |
| Continuous deployment  | Deployed to production automatically  | Automatic once the pipeline passes | Progressive rollout, automated abort, feature flags |

**Where GitOps fits.** GitOps is a way of implementing the delivery half. CI builds and tests the artefact, then opens a change to a deployment repository; an in-cluster agent such as Argo CD or Flux reconciles that change. If a human approves the production pull request, that is continuous delivery. If a bot merges it once staging evidence is green, that is continuous deployment. See [What is GitOps and what does it actually guarantee?](./what-is-gitops-and-what-does-it-actually-guarantee.md).

**Why the platform team cares.** The users here are product engineers who want their merged change running in production without learning the deployment machinery. A platform provides the shared pipeline, the artefact registry, the promotion mechanism, and the rollout controller, so each team gets continuous delivery by default and can opt into continuous deployment once its tests and alerts are good enough. The DORA metrics - deployment frequency, change lead time, change failure rate, failed deployment recovery time, and rework rate - are the usual way to show whether that platform is working.

**The trade-off.** Continuous deployment gives the shortest lead time and the smallest batch size, and small batches are easier to debug and roll back. The cost is that you need a mature testing and observability practice first; switching it on with a flaky test suite ships bugs faster. Regulated environments often stop at continuous delivery because a named approver is a control requirement - though an automated promotion pull request carrying the evidence can satisfy that without slowing things much.

## Example

```text
One change, three levels of automation.

  developer merges PR #812 to main
        |
  CONTINUOUS INTEGRATION ---------------------------------------------
        build + unit tests + lint                (every push, ~6 min)
        mainline stays green; a red build is fixed first
        |
  CONTINUOUS DELIVERY ------------------------------------------------
        image built once: ghcr.io/example/checkout@sha256:9f2c8b1d...
        SBOM, signature, vulnerability scan attached
        deployed to staging, integration tests pass
        promotion PR to production opened automatically
        |
        +--> a human approves the PR      = continuous DELIVERY
        |
        +--> a bot merges it when staging
             evidence is green            = continuous DEPLOYMENT
        |
  ROLLOUT (either way) -----------------------------------------------
        canary 5% -> 50% -> 100%, abort on error-budget burn
```

```yaml
# GitHub Actions: the CI half. Runs on every pull request and every merge.
name: ci
on:
  pull_request:
  push: { branches: [main] }
permissions:
  contents: read
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-go@v6
        with: { go-version: "1.25" }
      - run: go test ./...
```

## Interview tips

- Define all three and stress that they are cumulative. Many candidates use "CD" without saying which one they mean; being precise is the easy win.
- Say that CI is a practice - frequent integration into mainline - and that a CI server with month-long branches is not CI.
- The difference between delivery and deployment is exactly one thing: whether a human decides when to release. Everything technical is the same.
- Expect "what do you need before switching on continuous deployment?" Answer: trustworthy tests, progressive rollout with automated abort, and feature flags to separate deploy from release. See [What is progressive delivery?](../progressive-delivery-and-feature-flags/what-is-progressive-delivery.md).
- Name the platform's role: make continuous delivery the default for every team through a shared pipeline, and let teams graduate to continuous deployment.

---

[⬅ Back to GitOps and Continuous Delivery](./README.md) · [All topics](../README.md)
