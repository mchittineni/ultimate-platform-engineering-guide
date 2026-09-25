---
title: "How do you prepare for a platform engineering interview?"
id: 252
category: "Platform Engineering Interviews"
difficulty: "Beginner"
tags:
  - platform-engineering
  - platform-engineering-interviews
  - interview-questions
---

# How do you prepare for a platform engineering interview?

**Short answer:** Find out the shape of the loop, then prepare in order of return: a bank of four or five stories about your own platform work with numbers, two or three design prompts practised out loud, a troubleshooting method you can state in a sentence, and a refresh of the fundamentals you have not touched recently. Platform interviews are distinctive because they test whether you think about your users - the engineers who consume the platform - so every piece of preparation should include who the user was and what it saved them.

## Detail

**Start by finding out what the loop contains.** Ask the recruiter directly: how many rounds, what each is called, whether there is a live coding or infrastructure-as-code exercise, whether any round uses a real environment, and what the policy is on AI coding assistants. Recruiters expect these questions and usually answer them, and knowing that a loop has no algorithmic round but does have a live Terraform exercise changes how you spend your time. The typical loop is described in [What does a platform engineering interview loop look like?](./what-does-a-platform-engineering-interview-loop-look-like.md).

**Build a story bank before anything else.** Four or five real projects or situations, each written down as problem, users, what you changed, what happened to a number, and one decision with a trade-off. One well-understood project can supply a design discussion, an adoption story, a mistake, and a disagreement, so depth beats breadth. This is the preparation with the highest return because it feeds the behavioural round, the "walk me through something you built" round, and the design round, where interviewers love a candidate who can say "I did this for real, and here is what went wrong".

**Practise design prompts out loud.** Pick prompts that sound like platform work - "let forty teams provision databases themselves", "let teams deploy without cluster access", "design preview environments" - and talk through them to a friend or a recording. Reasoning you do not say does not score, and the first time you hear yourself explain an interface before any component should not be in the interview itself.

**Have a troubleshooting method, not a tool list.** Scope first (one service or all, one cluster or all, when did it start), then what changed, then work the layers from the user inward, saying what each observation rules out. Being able to state that in one breath is worth more than memorising flags.

**Refresh fundamentals honestly.** Engineers who have spent two years building abstractions often find their networking, Linux, and identity knowledge has faded. Spend a few evenings on what happens when a Deployment is applied, how a pod gets cloud credentials without a stored key (on EKS that is Pod Identity or IRSA; on GKE and AKS, workload identity federation), how DNS and load balancing reach a pod, and how a certificate is issued and renewed.

**Do something hands-on.** A local cluster with a small GitOps setup, a Terraform or OpenTofu module with tests, a short script against a cloud API. This keeps your hands fluent for any live exercise and gives you fresh, specific material to talk about.

**Prepare for the remote reality.** Most loops are now run over video, often with a shared editor or a cloud sandbox. Test your camera, microphone, screen share, and the editor they name. Expect identity checks and a request to keep your camera on; that has become common as fraudulent applications have grown.

**Know the AI policy and follow it exactly.** Some companies ban AI assistants in live rounds, some allow them openly, and some run rounds designed around them where they want to see how you prompt, review, and correct generated code. If the policy is not stated, ask. Using an assistant when it is not permitted is usually disqualifying, and if it is permitted, the assessment shifts to whether you can spot what it got wrong.

**Prepare your own questions.** They are part of the assessment. See [What should you ask your interviewer about their platform?](./what-should-you-ask-your-interviewer-about-their-platform.md).

**Trade-off: breadth versus depth.** You cannot refresh everything. For a senior platform role, weight stories and design; for an early-career role, weight fundamentals and the coding or automation exercise, while still having one or two stories about something you built for other engineers.

## Example

```text
A three-week preparation plan for a mid-level platform role, around a day job.

  WEEK 0  (one conversation)
    ask the recruiter: rounds and their names, any live IaC or coding exercise,
    real environment or whiteboard, AI assistant policy, video tool and editor

  WEEK 1  STORIES - the highest return
    write 5 stories, each on one page:
      problem | users | what I changed | the number | a decision + trade-off |
      what went wrong | what was mine vs the team's
    e.g. "self-service preview environments: 12 teams, median wait for a test
          environment 2 days -> 6 minutes; chose namespaces over clusters,
          gave up hard isolation; cleanup job missed orphaned volumes at first"

  WEEK 2  DESIGN AND TROUBLESHOOTING, out loud
    2 design prompts, 45 minutes each, recorded, then replayed
    check: did I ask about users first? interface before components?
           did I say what I would NOT build? did I state a success measure?
    1 troubleshooting drill with a friend playing the environment
    method, stated in one breath: "scope, what changed, layers inward,
                                   mitigate if there is impact, then prevent"

  WEEK 3  FUNDAMENTALS AND HANDS-ON
    evenings: Pod lifecycle, Services and DNS, workload identity, TLS renewal
    build: kind cluster + Argo CD syncing one app; a small OpenTofu module
           with a validation rule and a test
    write 6 questions to ask, split by hiring manager and engineer

  DAY BEFORE
    camera, microphone, screen share, the named editor; water; a notepad
    re-read the five story pages, nothing new
```

```bash
# A throwaway lab that keeps your hands fluent for a live exercise.
kind create cluster --name prep
kubectl create namespace argocd
kubectl apply -n argocd --server-side \
  -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl -n argocd rollout status deploy/argocd-server
```

## Interview tips

- Ask the recruiter what the loop contains, including the AI assistant policy. Preparing evenly for rounds that do not exist is the most common waste of preparation time.
- Write your stories down. A story you have only thought about tends to come out as a tool list; one you have written tends to come out as problem, users, number, and decision.
- Every story and every design answer should name the user - the engineers who consume the platform - and what it saved them. That is the thing platform interviews are listening for.
- Practise out loud, at least twice. Hearing yourself is the fastest way to find where you skip the reasoning.
- Refresh identity and networking even if you think you know them. They are the usual gaps for people who build abstractions.
- If AI assistants are allowed, practise with one and practise reviewing its output critically; if they are not, practise without one so the round does not feel unfamiliar.
- Stop learning new material the day before. Re-reading your own stories is more valuable than one more article.

---

[⬅ Back to Platform Engineering Interviews](./README.md) · [All topics](../README.md)
