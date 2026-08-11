---
title: "How do you give developers a fast inner development loop?"
id: 65
category: "Environments and Ephemeral Infrastructure"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - environments-and-ephemeral-infrastructure
  - interview-questions
---

# How do you give developers a fast inner development loop?

**Short answer:** Measure the edit-to-feedback cycle, then attack whatever dominates it - which is usually a container build and image push standing between a code change and a running process. The target is seconds, and the way to reach it is to avoid rebuilding images during development: sync the code into a running container, or run the service locally against remote dependencies. This is often the highest-value and most neglected developer experience investment a platform team can make.

## Detail

**Why the inner loop matters more than the pipeline.** A developer runs the inner loop dozens or hundreds of times a day; the pipeline runs a handful. A four-minute cycle is not merely slow, it changes behaviour - people batch changes, stop testing incrementally, and lose the flow state that makes debugging tractable. Cutting four minutes to ten seconds is worth more than shaving two minutes off CI.

**The loop to measure.** Edit code, build, containerise, push, deploy, wait for readiness, exercise, observe. In a naive Kubernetes workflow the middle four stages dominate completely, and none of them exist in a well-designed loop.

**The options, roughly in order of speed:**

| Approach                           | Cycle time | Fidelity                          |
| ---------------------------------- | ---------- | --------------------------------- |
| Native process, mocked deps        | ~1s        | Lowest - not the real environment |
| Native process, remote deps        | 1-3s       | Good - real dependencies          |
| File sync into a running container | 2-10s      | High - real runtime and cluster   |
| Rebuild image, redeploy            | 2-8 min    | High, and unusable as a loop      |

**File sync is usually the best default for containerised services.** Tools in this space watch the source, copy changed files into the running container, and restart the process in place - so the pod, its identity, its mounted secrets, and its network context all persist. You keep cluster fidelity and get a cycle measured in seconds.

**Running locally against remote dependencies is the other strong option**, particularly for languages with fast native tooling. The service runs on the laptop with a debugger attached, while its dependencies - databases, other services - are the real ones in a remote namespace, reached through a proxy that also routes traffic from the cluster back to the local process. Best debugging experience; requires a working proxy mechanism and reasonable network latency.

**Cloud development environments solve a different problem.** A remote workspace gives consistent tooling, fast dependency access, and no laptop setup, which is excellent for onboarding and for large repositories. It does not by itself make the loop fast - a remote environment doing an image rebuild each time is still slow. Combine it with sync or local-process approaches rather than treating it as a substitute.

**Language tooling is part of the platform's job.** Compiled languages need build caching that actually works - and getting that right is real, unglamorous engineering. Interpreted languages need hot reload configured correctly. Test selection matters too: running only the tests affected by a change turns a two-minute suite into a five-second one.

**Do not neglect the debugger.** A loop that requires adding log statements and redeploying is much slower than one where a debugger attaches to the running process. Making remote debugging work through the platform's tooling is a small piece of work with a disproportionate effect on how it feels to work in the system.

**Instrument the loop.** Ask teams to record their cycle time, or measure it from tooling. It is the metric most likely to be terrible and least likely to appear on a platform dashboard, which is precisely why publishing it tends to get it fixed.

## Example

```text
The same change - one line in a handler - measured through four loops.

NAIVE KUBERNETES LOOP
  edit                        2s
  docker build              45s
  push to registry          30s
  kubectl apply / rollout   15s
  pod pull + start          40s
  readiness probe           20s
  exercise                  10s
                          -----
  TOTAL                  ~2m42s     <- done 40x/day = ~1.8 hours of waiting

FILE SYNC INTO THE RUNNING POD
  edit                        2s
  sync changed files          1s     no build, no push, no new pod
  process restart in place    4s     identity, secrets, network context all kept
  exercise                   10s
                          -----
  TOTAL                     ~17s     ~10x faster, same cluster fidelity

LOCAL PROCESS + REMOTE DEPENDENCIES
  edit                        2s
  hot reload / rebuild        3s     native toolchain, incremental
  exercise                   10s     debugger attached; real remote DB and
                          -----      real neighbouring services
  TOTAL                     ~15s     best debugging; needs a working proxy

TEST-ONLY LOOP (most changes should live here)
  edit                        2s
  affected tests only         4s     test selection, not the whole suite
                          -----
  TOTAL                      ~6s
```

```yaml
# The platform ships the loop as a supported capability, not a wiki page of tips.
# .platform/dev.yaml, generated by the golden path scaffold
apiVersion: platform.example.com/v1
kind: DevLoop
metadata: { name: checkout }
spec:
  default: sync # what `platform dev` does with no arguments

  modes:
    sync:
      target: { namespace: previews-alice, deployment: checkout }
      watch: ["src/**/*.go", "templates/**"]
      # No image build. Files are copied in and the process restarts in place.
      onSync: { restart: "supervisorctl restart app" }
      ignore: ["**/*_test.go", "docs/**"]

    local:
      run: "go run ./cmd/checkout"
      # Dependencies are the REAL remote ones, reached through the proxy; cluster
      # traffic for this service is routed back to the local process.
      proxy:
        namespace: previews-alice
        intercept: checkout
        forward: [postgres, pricing, redis]
      debug: { port: 2345, adapter: dlv }

    test:
      # Only what the change affects - the difference between 4s and 2m.
      command: "go test -run $(platform affected-tests) ./..."
      watch: ["src/**/*.go"]
```

```text
The metric to publish, because it is the one nobody measures:

  $ platform devloop report --month 2026-07

  TEAM            p50 cycle   p90     MODE USED           NOTE
  team-web            8s      14s     sync (91%)          healthy
  team-payments      16s      31s     local (64%)         healthy
  team-search        11s      22s     sync (88%)          healthy
  team-data        2m 51s   4m 10s    rebuild (97%)   <-- NOT ADOPTED. Still
                                                          building images per
                                                          change. ~1.9 hrs/dev/day
                                                          of waiting.
  Action: sit with team-data and find out why sync does not work for them.
  Their answer is a platform bug report, not a training problem.
```

## Interview tips

- Open by insisting on measurement, then name the stages. The build-and-push segment dominating the loop is the finding, and it is the same in almost every organisation.
- The frequency argument is what justifies the investment: the inner loop runs hundreds of times a day, the pipeline a handful.
- File sync as the default for containerised services, with the specific benefit that pod identity, secrets, and network context persist, is the strongest technical recommendation.
- Distinguish cloud development environments from loop speed. They solve consistency and onboarding; a remote environment still rebuilding images is still slow.
- Test selection - running only affected tests - is cheap and frequently forgotten, and most changes should live in that loop rather than a deploy loop.
- Publishing cycle time per team, and treating a team stuck on the slow path as a platform bug report rather than a training problem, is the senior close.

---

[⬅ Back to Environments and Ephemeral Infrastructure](./README.md) · [All topics](../README.md)
