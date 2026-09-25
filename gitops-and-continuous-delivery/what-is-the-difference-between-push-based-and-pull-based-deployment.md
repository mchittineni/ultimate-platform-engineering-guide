---
title: "What is the difference between push-based and pull-based deployment?"
id: 83
category: "GitOps and Continuous Delivery"
difficulty: "Beginner"
tags:
  - platform-engineering
  - gitops-and-continuous-delivery
  - interview-questions
---

# What is the difference between push-based and pull-based deployment?

**Short answer:** In a push-based deployment, an external system - usually the CI pipeline - connects to the target environment and applies the change, so it needs credentials for that environment. In a pull-based deployment, an agent running inside the environment watches a source of truth such as a Git repository or an OCI registry and pulls changes in itself, so nothing outside needs credentials to get in. Pull is the model GitOps is built on; push is simpler to start with and still the norm for many non-Kubernetes targets.

## Detail

**Push: the pipeline does the deploying.** After building and testing, a CI job runs `kubectl apply`, `helm upgrade`, or a cloud deployment command against the target. It is easy to understand, the deployment appears as a step in the pipeline log, and failures show up where developers are already looking. The costs are structural:

- **Credentials live outside the cluster.** The CI system holds a credential for every environment it deploys to, which makes it the most valuable target in the organisation. OIDC federation can make those credentials short-lived, but the CI system still has the _ability_ to change production.
- **The cluster needs to be reachable.** The pipeline must be able to connect to each cluster's API server, which means exposing it or running self-hosted runners inside private networks.
- **State is only correct at the moment of deployment.** If someone changes the cluster by hand afterwards, nothing notices or corrects it until the next pipeline run.

**Pull: the environment deploys itself.** An agent such as Argo CD or Flux runs in the cluster, periodically fetches the desired state, compares it with what is running, and applies the difference. CI's job ends when it has published an image and committed a new reference to the deployment repository. The consequences are the mirror image of push:

- **No inbound access and no external cluster credentials.** The agent only needs read access to Git or a registry, and it connects outwards. Clusters in private networks, at the edge, or in customer environments can be managed without opening the API server.
- **Continuous reconciliation.** Because the agent keeps comparing, manual drift is detected and, if you enable self-heal, reverted. See [What is configuration drift and how does a platform detect it?](./what-is-configuration-drift-and-how-does-a-platform-detect-it.md).
- **Recovery is built in.** A rebuilt cluster with the agent installed converges on the same state without re-running every pipeline.

**The honest downsides of pull.** Feedback is less direct: a merged pull request does not mean the change is live, so developers need status surfaced somewhere - the Argo CD UI, a portal, or notifications back to the pull request. There is a delay between merge and apply unless you configure Git webhooks to trigger an immediate refresh rather than waiting for the next poll. Ordering across systems ("run the migration, then deploy, then update DNS") is harder when there is no single script. And the agent itself is now critical infrastructure that has to be upgraded and monitored.

**The hybrid that confuses people.** A single central Argo CD instance managing fifty clusters is pull from Git's perspective, but push from each workload cluster's perspective: the hub holds credentials for every spoke and connects to their API servers. That concentration of credentials is the same risk push-based CI has, just moved. Alternatives are one agent per cluster (the usual Flux shape), or hub-and-spoke designs where a lightweight agent in each spoke pulls its configuration from the hub, such as the `argocd-agent` project. Being able to explain this nuance is a good signal in an interview.

| Aspect                   | Push (CI deploys)                   | Pull (in-cluster agent)                    |
| ------------------------ | ----------------------------------- | ------------------------------------------ |
| Who holds cluster access | The CI system                       | Only the agent, inside the cluster         |
| Network direction        | CI -> cluster API (inbound)         | Agent -> Git/registry (outbound)           |
| Drift after deploy       | Undetected until next run           | Detected continuously, optionally reverted |
| Deployment feedback      | In the pipeline log                 | Needs UI, notifications, or status checks  |
| Non-Kubernetes targets   | Natural fit (VMs, serverless, SaaS) | Needs a controller for each target type    |
| Getting started          | Simple                              | Requires installing and running the agent  |

**The platform user.** Product engineers should not have to care which model is in use - they merge a change and see it arrive. The platform team chooses the model and then closes its gaps: with pull, that means posting sync and health status back to the pull request so developers get the same feedback push would have given them; with push, it means scoping and shortening the pipeline's credentials. Many platforms use both: pull for Kubernetes workloads, push for targets without a reconciler, like a CDN configuration or a serverless function.

## Example

```yaml
# PUSH - the pipeline applies to the cluster. It needs a route to the API server
# and a credential that can change production.
name: deploy
on:
  push: { branches: [main] }
permissions:
  contents: read
  id-token: write # federated, short-lived - better than a stored kubeconfig
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: aws-actions/configure-aws-credentials@v5
        with:
          role-to-assume: arn:aws:iam::<account-id>:role/ci-deployer
          aws-region: eu-west-1
      - run: aws eks update-kubeconfig --name prod-eu-1
      - run: kubectl apply -k overlays/production
```

```yaml
# PULL - CI only commits a new digest. Flux in the cluster notices and applies.
# No external system holds a cluster credential.
apiVersion: source.toolkit.fluxcd.io/v1
kind: GitRepository
metadata: { name: checkout-deploy, namespace: flux-system }
spec:
  interval: 1m # poll interval; a webhook Receiver can trigger immediately
  url: https://github.com/example/checkout-deploy
  ref: { branch: main }
---
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata: { name: checkout, namespace: flux-system }
spec:
  interval: 10m # full re-reconcile, which also corrects drift
  path: ./overlays/production
  prune: true
  sourceRef: { kind: GitRepository, name: checkout-deploy }
```

## Interview tips

- Define both by one question: who initiates the change and who holds the credentials? That framing makes the security argument obvious.
- Give pull a fair set of downsides - delayed and indirect feedback, cross-system ordering, and the agent as critical infrastructure. One-sided answers sound rehearsed.
- Raise the hub-and-spoke nuance yourself: a central Argo CD holding credentials for every cluster is push towards the spokes. It shows you think about where credentials actually live.
- If asked how to make push safer, answer with OIDC federation and narrowly scoped, short-lived roles. See [How do you run a secretless CI/CD pipeline?](../platform-security/how-do-you-run-a-secretless-ci-cd-pipeline.md).
- Mention that real platforms often mix the two - pull for Kubernetes, push for targets that have no reconciler - and that this is fine as long as it is a deliberate choice.

---

[⬅ Back to GitOps and Continuous Delivery](./README.md) · [All topics](../README.md)
