---
title: "What is self-service and why is it the defining property of a platform?"
id: 4
category: "Platform Engineering Fundamentals"
difficulty: "Beginner"
tags:
  - platform-engineering
  - platform-engineering-fundamentals
  - interview-questions
---

# What is self-service and why is it the defining property of a platform?

**Short answer:** Self-service means a product engineer can get a capability they need - a new service, a database, an environment, a secret, a dashboard - by stating what they want through an interface, and the platform delivers it without a human on the platform team doing the work. It is the defining property because it is what breaks the link between the number of requests and the size of the platform team. Without it, you have a helpful operations team; with it, you have a platform.

## Detail

**What self-service actually is.** A self-service capability has three parts: an interface the developer uses (a file in their repository, a CLI command, a portal form, an API call), automation that turns that request into real infrastructure, and guardrails that decide what is allowed without a person checking each request. The developer states intent - "I need a small Postgres database with daily backups" - and the platform handles the how: the cloud resource, the network placement, the credentials, the monitoring, the cost tags.

**Why it is the defining property, not one feature among many.** Consider the alternative. If each database request becomes a ticket, a platform engineer spends an hour writing Terraform, and the team waits two days. Double the number of product teams and you double the tickets, so the platform team must grow in step with the organisation. That is a linear service, and it becomes the bottleneck it was meant to remove. Self-service turns the platform team's work into something done _once_ - building the capability - rather than once per request. That change in cost shape is the whole economic argument for platform engineering.

**Who the user is and what they save.** The user is the product engineer on a stream-aligned team. What self-service saves them is not just waiting time. It removes the need to learn the cloud provider's database options, the network design, the backup policy, and the secret store before they can do their actual job. That reduction in cognitive load is why self-service matters even when the ticket queue is short. See [what cognitive load is and why it drives platform design](../developer-experience/what-is-cognitive-load-and-why-does-it-drive-platform-design.md).

**Self-service is not the same as unrestricted access.** Handing every team admin rights to the cloud account is self-service in a narrow sense, but it pushes all the complexity back onto them and removes any consistency. Good self-service is _bounded_: a small set of options with safe defaults, and policy that rejects unsafe requests automatically. The guardrails are what let you remove the human approver - you replace a person reviewing each request with rules that encode what that person would have checked. The mechanics of doing this safely are covered in [providing self-service infrastructure without handing out cloud credentials](../control-planes-and-abstractions/how-do-you-provide-self-service-infrastructure-without-handing-out-cloud-credentials.md).

**How to test whether something is self-service:**

- Can a developer complete it outside the platform team's working hours?
- Does the time to fulfil it stay the same when request volume doubles?
- Is there any step where a platform engineer has to read, approve, or type something?
- Does the developer find out about a rejected request immediately, with a reason, rather than in a ticket comment later?

If any step needs a human for routine requests, that step is where the next piece of platform work should go.

**The trade-offs.** Building a self-service capability costs far more than fulfilling one request by hand, so automating something requested twice a year is waste. The platform team also takes on the reliability of the automation: when the provisioning controller is down, nobody gets a database. And bounded options will not fit every case, so you need a documented way for teams with unusual needs to step outside them. The usual rule is to fulfil a request by hand the first few times, learn what people actually ask for, and automate once the pattern and the volume are clear.

## Example

```text
The same request - "the checkout team needs a staging database" - two ways.

Ticket-driven (not self-service)
  Day 0  Developer files ticket: "need Postgres for staging, not sure what size"
  Day 1  Platform engineer asks follow-up questions in the ticket
  Day 2  Engineer writes Terraform, opens PR, waits for review
  Day 3  Applied. Credentials sent over chat. Monitoring forgotten.
         Cost: ~3 hours of platform time per request, every request.

Self-service
  Developer adds four lines to the service's spec and opens a pull request:
```

```yaml
# platform/service.yaml in the checkout repository
dependencies:
  - postgres:
      size: small # one of: small | medium | large - no instance types
      backups: daily # policy rejects "none" for tier 1 services
      environment: staging
```

```text
  Minute 0   CI validates the spec against policy; merge
  Minute 2   Controller provisions the database in the private network
  Minute 9   Credentials written to the secret store, mounted into the service;
             dashboard and backup alert created; cost tagged to team-payments
             Cost: zero platform time for this request.
```

## Interview tips

- Define self-service by the absence of a human in the routine path, and explain why that matters economically: platform effort stops scaling with request volume.
- Always pair self-service with guardrails. Candidates who describe self-service as "give teams access" miss the point - bounded options and automated policy are what make removing the approver safe.
- Name the user and what they save: the product engineer, and both waiting time and the knowledge they would otherwise need.
- Expect "is a ticket ever acceptable?" - yes, for rare or genuinely novel requests, and as a way to learn what to automate next. The mistake is leaving high-volume requests on a queue.
- A strong close is the test: "can a new engineer get this at 2am without waking anyone up?"

---

[⬅ Back to Platform Engineering Fundamentals](./README.md) · [All topics](../README.md)
