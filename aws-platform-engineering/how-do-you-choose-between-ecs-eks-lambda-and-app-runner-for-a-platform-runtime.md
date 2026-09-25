---
title: "How do you choose between ECS, EKS, Lambda, and App Runner for a platform runtime?"
id: 152
category: "AWS Platform Engineering"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - aws-platform-engineering
  - interview-questions
---

# How do you choose between ECS, EKS, Lambda, and App Runner for a platform runtime?

**Short answer:** Choose by the operational burden you are willing to own and the workload shape, not by capability. Lambda for event-driven and spiky work with short executions; ECS Express Mode for straightforward HTTP services where you want almost no operational surface (App Runner used to fill this slot, but it closed to new customers on 30 April 2026); ECS on Fargate when you want containers without a control plane to run; EKS when you need the Kubernetes ecosystem, custom controllers, or portability. A platform should support one primary runtime plus one specialised, not all four.

## Detail

**Supporting a runtime is a permanent commitment.** Each one needs its own golden path, deployment mechanism, observability wiring, IAM patterns, upgrade story, cost model, and documentation. A platform team offering four runtimes has four of everything and none of them excellent. The single most valuable decision here is to pick a primary and be deliberate about the exception.

**The comparison in the terms that decide it:**

| Runtime     | You operate                  | Best for                                       | Main constraint                                         |
| ----------- | ---------------------------- | ---------------------------------------------- | ------------------------------------------------------- |
| Lambda      | Nothing                      | Event-driven, spiky, glue, short tasks         | Execution time limit, cold starts, per-invocation model |
| App Runner  | Nothing                      | Existing customers only; closed to new ones    | No new features planned; migrate to ECS Express Mode    |
| ECS/Fargate | Task definitions             | Containers, no control plane to manage         | AWS-specific; thinner ecosystem                         |
| EKS         | A cluster and its components | Kubernetes ecosystem, controllers, portability | By far the largest operational surface                  |

**EKS is the right answer when the ecosystem is the point.** If your platform is built on custom resources, admission control, Crossplane, a service mesh, or GitOps reconciliation, you need Kubernetes - those things do not exist elsewhere. The cost is a genuine fleet of components to upgrade, and that cost is the whole of the platform-engineering conversation about Kubernetes.

**ECS on Fargate is underrated for platform teams.** It gives you containers, IAM per task, service discovery, and load balancer integration with no control plane, no node upgrades, and no CNI to debug. For an organisation whose workloads are ordinary HTTP services and asynchronous workers, and which does not need Kubernetes-specific tooling, it is a much smaller operational surface for a similar outcome. Being able to recommend it rather than defaulting to Kubernetes signals judgement.

**Lambda is a workload-shape decision, not a philosophy.** It fits event handling, scheduled work, glue between services, and spiky traffic where paying per invocation beats paying for idle capacity. It fits badly for long-running processing, workloads needing large local state, latency-critical paths sensitive to cold starts, and anything where the per-invocation cost at sustained high volume exceeds a container running continuously. The crossover point is worth calculating rather than assuming.

**App Runner is now a legacy answer.** It suited a narrow, real case - a containerised HTTP service deployed with minimal ceremony - but AWS closed it to new customers on 30 April 2026. Existing customers can keep using it and AWS continues security and availability work, but no new features are planned. AWS points customers at **Amazon ECS Express Mode** (launched November 2025), which takes a container image and provisions a Fargate service with a load balancer, HTTPS endpoint, and autoscaling in one step, while leaving the full ECS feature set available when a team outgrows the defaults. For a platform this is a better shape anyway: the "simple" path and the "full" path are the same runtime, so graduating does not mean a migration. The broader lesson is worth saying in an interview - a thin PaaS layer on a hyperscaler can be withdrawn, which is another argument for a platform interface that keeps the runtime an implementation detail.

**Mixed estates are normal; unbounded ones are not.** A defensible shape is one primary runtime carrying most services, plus Lambda for event-driven work, with anything else requiring a recorded justification. What you want to avoid is four runtimes chosen by team preference, because then the platform's paved road is four paved roads.

**The platform interface should outlast the choice.** If teams declare a `Service` and the platform decides how it runs, you can move a workload between runtimes without touching its repository. That is the strongest position: the runtime becomes an implementation detail rather than something baked into every service.

## Example

```text
Choosing, in the order the questions actually matter:

  Do you need Kubernetes-specific tooling - CRDs, admission control, operators,
  Crossplane, a service mesh, GitOps reconciliation of arbitrary resources?
    yes -> EKS. Accept the fleet management cost; it is the price of the ecosystem.
    no  -> continue

  Is the workload event-driven or spiky, with short executions?
    yes -> Lambda. Calculate the crossover: at sustained high invocation rates a
           continuously running container is usually cheaper.
    no  -> continue

  Is it an ordinary HTTP service or async worker with no unusual requirements?
    yes -> ECS on Fargate. Containers, IAM per task, no control plane to operate.
           ECS Express Mode if you want even less surface to start with - it is
           the same runtime, so outgrowing it is not a migration.
    no  -> continue

  Do you need portability across clouds, or is your platform already Kubernetes?
    yes -> EKS

  Then: pick ONE primary and support Lambda alongside it. Four runtimes means
  four golden paths, four observability integrations, four upgrade stories.
```

```text
A defensible estate for 220 services:

  PRIMARY: EKS ................................ 178 services
    justification: the platform is built on CRDs, Kyverno, Crossplane, and Argo CD.
    Those do not exist without Kubernetes, and they are what makes self-service work.

  Lambda ....................................... 38 functions
    event handlers (S3, EventBridge), scheduled jobs, glue between services.
    A workload-shape fit, not a second platform.

  ECS/Fargate ................................... 4 services
    three vendor-supplied containers that dislike the mesh sidecar, plus one
    workload needing a long-lived task with no cluster dependency.
    Each has a recorded justification.

  App Runner .................................... 0
    closed to new customers since April 2026; the two services a team had
    started on it were moved to ECS Express Mode, then onto the platform's
    own Service path.

  Note what this is NOT: four runtimes chosen by team preference. One primary,
  one shape-based fit, and four recorded exceptions.
```

```yaml
# The interface that outlasts the choice. `runtime: auto` lets the platform
# place the workload; moving it later touches no service repository.
apiVersion: platform.example.com/v1
kind: Service
metadata: { name: receipt-generator }
spec:
  owner: group:team-payments
  tier: 2
  runtime: auto # or: eks | fargate | lambda - platform decides by shape
  shape: event-driven # informs the decision
  trigger:
    events: [{ source: s3, bucket: example-team-payments-receipts, on: created }]
  execution:
    maxDuration: 30s # short -> Lambda is a good fit
    concurrency: { max: 200 }
  # If this later grows a 10-minute execution, the platform moves it to a
  # container runtime and this file barely changes.
```

## Interview tips

- Open with the platform-team framing: each supported runtime is a permanent commitment to a golden path, observability wiring, IAM patterns, and an upgrade story. That is what makes this a platform question rather than a service question.
- Be able to say EKS is not automatically right, and give the specific condition that makes it right - you need the Kubernetes ecosystem for your own platform machinery.
- Recommending ECS on Fargate where Kubernetes is not needed is the judgement signal here. Many candidates default to Kubernetes without examining the operational cost.
- Know that App Runner closed to new customers in April 2026 and that ECS Express Mode is AWS's suggested replacement. Recommending App Runner for a new platform today is a currency red flag.
- For Lambda, frame it as a workload-shape fit and mention calculating the crossover point rather than assuming serverless is cheaper.
- "One primary plus one specialised, with recorded exceptions" is the defensible answer to the mixed-estate question.
- The strongest close is that the platform interface should outlast the runtime choice, so a workload can move between runtimes without its repository changing.

---

[⬅ Back to AWS Platform Engineering](./README.md) · [All topics](../README.md)
