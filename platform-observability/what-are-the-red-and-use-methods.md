---
title: "What are the RED and USE methods?"
id: 214
category: "Platform Observability"
difficulty: "Beginner"
tags:
  - platform-engineering
  - platform-observability
  - interview-questions
---

# What are the RED and USE methods?

**Short answer:** They are two checklists for deciding what to measure. RED - Rate, Errors, Duration - is for request-driven services and describes what users experience. USE - Utilisation, Saturation, Errors - is for resources such as CPU, memory, disks, and connection pools, and describes whether the machinery underneath is coping. A platform usually generates RED dashboards for every service and USE dashboards for every node, cluster, and shared component.

## Detail

**RED: measure the service from the caller's point of view.** Tom Wilkie proposed RED for microservices. For every service, and ideally for every endpoint, track:

- **Rate** - requests per second.
- **Errors** - failed requests per second, or as a fraction of rate.
- **Duration** - the distribution of request latency, as a histogram so you can read percentiles.

RED works because it is uniform. Every request-serving service can be described by the same three numbers, so one dashboard template covers the whole estate, and an on-call engineer who has never seen a service can still read its health. RED maps closely onto the "golden signals" from Google's SRE book, which add saturation as a fourth.

**USE: measure the resource from the inside.** Brendan Gregg's USE method says that for every resource, check:

- **Utilisation** - the proportion of time or capacity the resource is busy, such as CPU at 70%.
- **Saturation** - work that is queued because the resource is full, such as the run queue length, memory swapping, or requests waiting for a database connection.
- **Errors** - error events for the resource, such as disk I/O errors or dropped packets.

Saturation is the one people forget, and often the most important. A CPU at 100% utilisation that has no queue is working hard; a CPU at 80% with a long run queue, or a container being CPU throttled, is making requests wait. On Kubernetes, CPU throttling from limits is a classic saturation signal that utilisation hides.

**They answer different questions and are used together:**

| Method | Applies to                               | Question it answers           | Typical owner          |
| ------ | ---------------------------------------- | ----------------------------- | ---------------------- |
| RED    | Services, endpoints, APIs                | Are users being served well?  | Service team           |
| USE    | CPU, memory, disk, network, pools, nodes | Is a resource the bottleneck? | Platform or infra team |

A typical investigation starts with RED - checkout's latency is up - and moves to USE to find the cause - the database connection pool is saturated. RED tells you there is a problem and where users feel it; USE tells you which resource is responsible.

**Why RED suits alerting.** RED measures symptoms users experience, so it makes a good basis for SLOs and paging. USE metrics are mostly causes: high CPU on its own is not a reason to wake someone if users are fine. A sound practice is to page on RED-based SLO burn and use USE dashboards to diagnose.

**The trade-offs and limits.** RED does not fit batch jobs or queue consumers well; for those, measure throughput, lag, and job success and duration instead. Averages are misleading for duration, so always use histograms and percentiles. USE requires knowing every resource, including soft ones such as thread pools, file descriptors, and rate limits from dependencies, which are easy to miss.

**How a platform uses them.** The platform's users are product engineers who want to know "is my service healthy?" without designing dashboards. OpenTelemetry's HTTP and gRPC instrumentation emits standard duration histograms, so the platform can derive RED for every service automatically from `http.server.request.duration`. USE comes from the node, container, and kubelet metrics the platform already collects. Generating both from templates means every service gets the same views on its first deploy, and improving the template improves every service at once.

## Example

```promql
# RED for one service, from the OpenTelemetry HTTP server duration histogram
# (exported to Prometheus as http_server_request_duration_seconds).

# Rate: requests per second
sum(rate(http_server_request_duration_seconds_count{service_name="checkout"}[5m]))

# Errors: fraction of requests returning 5xx
sum(rate(http_server_request_duration_seconds_count{service_name="checkout", http_response_status_code=~"5.."}[5m]))
  / sum(rate(http_server_request_duration_seconds_count{service_name="checkout"}[5m]))

# Duration: p99 latency by route
histogram_quantile(0.99,
  sum by (le, http_route) (rate(http_server_request_duration_seconds_bucket{service_name="checkout"}[5m])))
```

```promql
# USE for containers and nodes, from cAdvisor and node exporter.

# Utilisation: CPU used by a pod against its request
sum by (pod) (rate(container_cpu_usage_seconds_total{namespace="team-payments", container!=""}[5m]))
  / sum by (pod) (kube_pod_container_resource_requests{namespace="team-payments", resource="cpu"})

# Saturation: share of CPU periods in which the container was throttled
sum by (pod) (rate(container_cpu_cfs_throttled_periods_total{namespace="team-payments"}[5m]))
  / sum by (pod) (rate(container_cpu_cfs_periods_total{namespace="team-payments"}[5m]))

# Errors: network receive errors per node
sum by (instance) (rate(node_network_receive_errs_total[5m]))
```

```text
An investigation that uses both:

  RED   checkout p99 latency 280ms -> 2.1s, error rate normal, rate normal
        -> users feel it; something is slow, not failing
  RED   outbound: postgres client span p99 1.9s
  USE   postgres connection pool: utilisation 100%, 40 requests waiting  <-- saturation
  USE   postgres host CPU 35%, disk fine
        -> the database is not the bottleneck; the pool size is.
```

## Interview tips

- Expand both acronyms correctly and say who each is for: RED for request-driven services, USE for resources.
- Emphasise saturation. Utilisation can look fine while work queues up, and CPU throttling on Kubernetes is the example interviewers like.
- Explain how they combine: RED finds the symptom users feel, USE finds the resource causing it.
- Say that RED is the better basis for alerting because it measures symptoms; USE is mostly for diagnosis.
- Mention the gaps: batch jobs and queue consumers need throughput, lag, and success metrics instead, and duration must be a histogram, never an average.
- Tie it to the platform: RED and USE dashboards generated for every service and node from standard metrics, so nobody has to build them. See also [What telemetry should every service get without writing code?](./what-telemetry-should-every-service-get-without-writing-code.md).

---

[⬅ Back to Platform Observability](./README.md) · [All topics](../README.md)
