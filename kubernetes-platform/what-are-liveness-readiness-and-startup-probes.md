---
title: "What are liveness, readiness, and startup probes?"
id: 57
category: "Kubernetes Platform"
difficulty: "Beginner"
tags:
  - platform-engineering
  - kubernetes-platform
  - interview-questions
---

# What are liveness, readiness, and startup probes?

**Short answer:** They are health checks the kubelet runs against each container, and each one triggers a different action. A readiness probe failing removes the Pod from Service endpoints, so it stops receiving traffic but keeps running. A liveness probe failing restarts the container. A startup probe holds off the other two until a slow-starting application has finished booting. Getting them wrong is one of the most common causes of self-inflicted outages, so a platform should ship sensible defaults and warn about the dangerous patterns.

## Detail

**How a probe works.** The kubelet on the node runs the check on a schedule - an HTTP GET (any 2xx or 3xx is success), a TCP connection, a gRPC health check, or a command executed inside the container. `periodSeconds` sets the interval, `timeoutSeconds` how long to wait, and `failureThreshold` how many consecutive failures count as failed. The probe runs locally, so it tests the container, not the network path a real user takes.

**Readiness: "should I get traffic right now?"** When readiness fails, the Pod's endpoint is marked not ready and Services, Gateways, and load balancers stop sending it new requests. Nothing is restarted. This is for temporary conditions: still warming a cache, shedding load, or draining during shutdown. It is also what makes rolling updates safe - a Deployment waits for new Pods to become ready before removing old ones, so a new version that never becomes ready stalls the rollout instead of taking the service down.

**Liveness: "is this process beyond saving?"** When liveness fails, the kubelet kills the container and restarts it according to the Pod's restart policy. It exists for one situation: a process that is still running but permanently stuck - a deadlock, an exhausted thread pool that will never recover. A restart is the only fix, so the probe automates it.

**Startup: "has it finished booting yet?"** While a startup probe is defined and has not yet succeeded, liveness and readiness probes do not run. Once it succeeds, it stops and the others take over. This solves the old dilemma of a JVM service that takes 90 seconds to start: without a startup probe you either set a long `initialDelaySeconds` on liveness (slow detection forever) or a short one (the container is killed mid-boot, restarts, and never comes up - a crash loop caused entirely by the probe).

| Probe     | Question it answers             | On failure                         | Typical check             |
| --------- | ------------------------------- | ---------------------------------- | ------------------------- |
| Startup   | Has the app finished starting?  | Keeps waiting; kills after budget  | Same endpoint as liveness |
| Readiness | Can it serve traffic right now? | Removed from endpoints, not killed | Can it do useful work     |
| Liveness  | Is it irrecoverably stuck?      | Container restarted                | Is the process responsive |

**The mistakes that cause outages.**

- **Liveness that checks dependencies.** If the liveness endpoint calls the database and the database has a blip, every replica fails liveness at once and Kubernetes restarts the whole fleet - turning a brief dependency problem into a full outage and a thundering herd on recovery. Liveness should check only the process itself.
- **Readiness that checks shared dependencies.** Subtler: if every replica goes unready because a shared downstream is slow, the Service has zero endpoints and clients get connection errors instead of a graceful degraded response. Readiness should reflect whether _this_ Pod can serve, not the health of the world.
- **Identical liveness and readiness probes** with the same thresholds, so an overloaded Pod is restarted rather than briefly taken out of rotation - which removes capacity exactly when it is needed.
- **Timeouts too tight for garbage-collection pauses**, so a healthy Pod under load gets restarted.
- **No readiness probe at all**, so traffic arrives before the application is listening and every deploy produces a burst of errors.

**Where the platform comes in.** Most developers copy a probe block from somewhere and never revisit it. The platform can do better: default probes in the service template pointing at conventional endpoints (`/livez`, `/readyz`), a startup probe with a generous budget, a liveness probe that is less aggressive than readiness, and a check in CI or admission that warns when liveness and readiness are identical or when a liveness path looks like it calls a dependency. Probes also interact with other platform defaults - the readiness gate is part of what makes node drains during [fleet upgrades](./how-do-you-upgrade-a-fleet-of-clusters-without-breaking-tenants.md) safe.

**The trade-off.** Aggressive probes detect real failures faster and cause false-positive restarts under load; relaxed probes are stable and slower to react. Readiness can reasonably be sensitive, because its action is cheap. Liveness should be conservative, because its action is destructive.

## Example

```yaml
# Platform default probes for a JVM HTTP service. The developer supplies the
# port; the platform supplies the shape.
apiVersion: apps/v1
kind: Deployment
metadata: { name: orders-api, namespace: team-orders }
spec:
  replicas: 3
  selector: { matchLabels: { app: orders-api } }
  template:
    metadata: { labels: { app: orders-api } }
    spec:
      containers:
        - name: app
          image: registry.example.com/team-orders/orders-api:2.14.0
          ports: [{ name: http, containerPort: 8080 }]
          startupProbe: # up to 30 x 5s = 150s to boot before liveness applies
            httpGet: { path: /livez, port: http }
            periodSeconds: 5
            failureThreshold: 30
          readinessProbe: # sensitive: cheap action, drop out of rotation fast
            httpGet: { path: /readyz, port: http } # checks local readiness only
            periodSeconds: 5
            failureThreshold: 2
          livenessProbe: # conservative: destructive action, only when truly stuck
            httpGet: { path: /livez, port: http } # process health, never the database
            periodSeconds: 10
            timeoutSeconds: 3
            failureThreshold: 6 # about a minute of consecutive failure
```

```text
Incident pattern worth recognising - liveness checking a dependency:

  10:02  primary database fails over (expected, ~40s)
  10:02  /health on every orders-api Pod returns 503 (it queries the database)
  10:03  liveness failureThreshold reached on all 3 replicas simultaneously
  10:03  all containers restarted; JVM warm-up takes 60s
  10:03  database is back - but no Pod is ready to serve
  10:05  3 cold replicas take full traffic; latency spike, timeouts, retries
         40-second dependency blip became a 3-minute full outage.

  Fix: liveness -> /livez (process only). Readiness -> /readyz (local state).
       Degrade gracefully on database errors inside the request path.
```

## Interview tips

- Give the action for each probe, not just the name: readiness removes from endpoints, liveness restarts, startup gates the other two. The action is what the interviewer is checking.
- The liveness-checks-the-database mistake, and how it turns a dependency blip into a fleet-wide restart, is the single most valuable point to make.
- Explain why startup probes exist - slow boots forced a choice between slow detection and crash loops.
- Say readiness can be sensitive because its action is cheap, and liveness conservative because its action is destructive. That principle covers most tuning questions.
- From the platform side, mention default probes in templates and a lint that flags identical liveness and readiness probes. Probes are a reliability default, not something every team should rediscover.

---

[⬅ Back to Kubernetes Platform](./README.md) · [All topics](../README.md)
