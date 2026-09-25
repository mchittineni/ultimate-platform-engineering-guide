---
title: "What does Cloud Run manage for you?"
id: 174
category: "GCP Platform Engineering"
difficulty: "Beginner"
tags:
  - platform-engineering
  - gcp-platform-engineering
  - interview-questions
---

# What does Cloud Run manage for you?

**Short answer:** Cloud Run takes a container image and runs it without you managing servers, clusters, or node pools: it provisions sandboxed instances, scales them with traffic - down to zero when idle - terminates TLS on an HTTPS endpoint, keeps every deployment as an immutable revision you can split traffic between, and wires logs and metrics into Cloud Logging and Monitoring. You still own the container, its configuration, its identity, who may call it, and making the application safe to run as many short-lived, stateless copies.

## Detail

**The unit you hand over is a container.** You build an image that listens on the port in the `PORT` environment variable (8080 by default), push it to Artifact Registry, and deploy it as a **service**. Cloud Run is not tied to a language or framework, which is what separates it from older function-as-a-service products. Cloud Functions has itself been folded in as Cloud Run functions, so functions are now simply source-based deploys onto the same runtime.

**What Cloud Run manages:**

| Concern       | Managed by Cloud Run                                                            |
| ------------- | ------------------------------------------------------------------------------- |
| Compute       | Instances are created, patched, and replaced for you; each runs in a sandbox    |
| Scaling       | Instances added as requests arrive and removed when idle, including to zero     |
| Endpoint      | A stable HTTPS URL with a managed certificate; HTTP/2 and WebSockets supported  |
| Releases      | Every deploy creates an immutable revision; traffic can be split or rolled back |
| Observability | Request logs, container stdout, and request metrics collected without an agent  |
| Availability  | Instances spread across zones in the region automatically                       |

**Scaling is driven by concurrency.** Each instance handles up to a configured number of simultaneous requests (80 by default). When requests exceed what the current instances can take, Cloud Run starts more, up to a maximum you set. When traffic stops, instances are shut down, and with a minimum of zero you stop paying for compute while idle. That is the most important cost property of Cloud Run and why it suits internal tools and preview environments so well.

**Revisions make releases safe by default.** A revision is an immutable snapshot of image plus configuration. Deploying creates a new one, and you choose how traffic divides - 100% to the new revision, or a canary such as 5%, or a tagged revision that receives no public traffic but has its own URL for testing. Rolling back is moving traffic to an older revision, which takes seconds because nothing is rebuilt.

**Beyond HTTP services.** Cloud Run also runs **jobs** - containers that run to completion, optionally as many parallel tasks, for batch and scheduled work - and **worker pools**, generally available since April 2026, for pull-based background consumers that do not serve requests at all. Services and jobs can attach GPUs for inference.

**What you still own.** This is the half interviewers care about:

- **Statelessness.** Instances can be stopped at any time, and local disk is in-memory and disappears. State lives in Cloud SQL, Firestore, Memorystore, or Cloud Storage.
- **Concurrency safety.** Concurrency above one means one process handles several requests at once, so shared in-process state must be thread-safe. That is an application property, not a setting.
- **Cold starts.** The first request to a new instance waits for the container to start. Small images and fast start-up help; a minimum instance count removes the problem but also removes the scale-to-zero saving.
- **Identity and access.** Each service runs as a service account you choose, and each service decides who may invoke it - public, or only principals holding `roles/run.invoker`. Ingress settings further restrict whether it is reachable from the internet at all.
- **Networking to private resources.** Reaching a database on a private IP needs Direct VPC egress into a subnet you provide.

**Who uses this, and what the platform gives them.** The users are product teams who want to ship an HTTP service or a worker without learning Kubernetes. The platform's job is to make the right configuration the default: a template that sets a dedicated service account, internal-only ingress unless a team asks otherwise, VPC egress into the right Shared VPC subnet, images pulled only from the organisation's Artifact Registry, and sensible scaling limits. Teams supply the image and a few values; the platform supplies the rest.

**The trade-off.** You give up control in exchange for not operating anything. No DaemonSets, no sidecar-heavy service mesh patterns, no custom kernel settings, and you work within Cloud Run's limits on request timeout, memory, and CPU per instance. When a platform needs the Kubernetes API itself, GKE is the better fit - see [How do you choose between GKE, GKE Autopilot, and Cloud Run?](./how-do-you-choose-between-gke-gke-autopilot-and-cloud-run.md).

## Example

```bash
# Deploy: private by default, its own identity, scale to zero.
gcloud run deploy checkout \
  --project=checkout-prod --region=europe-west1 \
  --image=europe-docker.pkg.dev/artifacts-prod/containers/checkout:1.15.0 \
  --service-account=sa-checkout@checkout-prod.iam.gserviceaccount.com \
  --no-allow-unauthenticated \
  --ingress=internal-and-cloud-load-balancing \
  --concurrency=80 --min-instances=0 --max-instances=50 \
  --no-traffic --tag=canary      # new revision gets a test URL, no live traffic

# Move 10% of live traffic to the canary, watch errors, then promote.
gcloud run services update-traffic checkout \
  --project=checkout-prod --region=europe-west1 --to-tags=canary=10

gcloud run services update-traffic checkout \
  --project=checkout-prod --region=europe-west1 --to-latest

# Allow exactly one caller - the frontend's service account - to invoke it.
gcloud run services add-iam-policy-binding checkout \
  --project=checkout-prod --region=europe-west1 \
  --member="serviceAccount:sa-web@web-prod.iam.gserviceaccount.com" \
  --role="roles/run.invoker"
```

```text
What the team wrote vs what Cloud Run did:

  team supplied:     image, service account, 5 flags
  Cloud Run did:     created revision checkout-00042-kav
                     issued https://checkout-...-ew.a.run.app with TLS
                     scaled 0 -> 7 instances at 09:00, 7 -> 0 by 19:40
                     split traffic 90/10 between revisions 00041 and 00042
                     shipped request logs and latency metrics to Cloud Monitoring
  team did NOT do:   patch an OS, size a node pool, install a log agent
```

## Interview tips

- Split the answer into "what Cloud Run manages" and "what you still own". The second list - statelessness, concurrency safety, cold starts, identity, private networking - is what distinguishes a real answer.
- Explain concurrency-based scaling and scale to zero as one mechanism, and connect scale to zero to cost for non-production.
- Mention revisions and traffic splitting: they give canaries and instant rollback with no extra tooling, which is a strong platform argument.
- Be precise that `--no-allow-unauthenticated` plus `roles/run.invoker` is service-to-service authorisation, and that ingress settings are a separate network-level control.
- Show you are current: Cloud Functions is now Cloud Run functions, and jobs, worker pools, and GPUs extend Cloud Run beyond request-serving.
- Name the limit that sends teams to GKE: needing the Kubernetes API, node-level agents, or long-lived stateful processes.

---

[⬅ Back to GCP Platform Engineering](./README.md) · [All topics](../README.md)
