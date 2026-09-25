---
title: "How do you answer 'tell me about yourself' for a platform role?"
id: 254
category: "Platform Engineering Interviews"
difficulty: "Beginner"
tags:
  - platform-engineering
  - platform-engineering-interviews
  - interview-questions
---

# How do you answer 'tell me about yourself' for a platform role?

**Short answer:** In about ninety seconds: who you are now and who you build for, one or two pieces of work with an outcome for those users, and why this role is the next step. It is not a request for your life story or a recital of your CV - it is the interviewer asking where to point the next forty-five minutes, so give them two or three threads worth pulling, each of which shows you think about the engineers who use the platform.

## Detail

**Understand what the question is for.** It opens almost every round, including technical ones, and it does three things for the interviewer: it calibrates your level, it gives them topics to ask about, and it shows how you communicate under mild pressure. A rambling answer wastes their time and yours; a crisp one steers the conversation towards your strongest material.

**Use present, past, future.** Present: your current role, the scope, and who your users are. Past: one or two pieces of work, each with a concrete outcome, chosen because they are relevant to this role. Future: why this job, specifically, is what you want next. That structure is easy to remember and naturally ends by handing the conversation back.

**Name your users early.** The platform-specific move is to describe your job in terms of who consumes it. "I am on a six-person platform team serving about forty product teams" frames everything that follows as product work for engineers. "I work with Kubernetes and Terraform" frames it as tooling, and the interviewer learns nothing they could not read on your CV.

**Pick work that plants a hook.** Choose one achievement with a number and one decision or lesson you would enjoy being asked about. If you mention that you moved 120 services off stored cloud keys, expect "how did you get teams to migrate?" - and have the answer ready. The opening is the only part of the interview where you choose the topic, so choose one you have prepared to depth.

**Keep it short, then stop.** Ninety seconds to two minutes. Stop after the future part rather than trailing off with "so, yeah". Silence after a clear ending is fine; it is the interviewer's turn.

**Adapt it to the round.** With a recruiter, emphasise scope, motivation, and fit. With an engineer before a technical round, lean on the technical thread. With a hiring manager, include how you work with other teams and what you want to grow into. The facts do not change; the emphasis does.

**If you are early in your career or changing into platform work,** use the same structure with what you have: an internal tool you built that colleagues used, automation that removed a manual step for a team, a support rotation where you noticed the same request recurring and fixed its cause. The instinct to build for other engineers is what is being looked for, and you can show it without the title.

**Trade-off: rehearsed versus natural.** Rehearse the structure and the two hooks, not a script. A memorised paragraph sounds memorised, and on video the lack of eye contact while you recall it is visible. Know the three beats and say them in your own words each time.

## Example

```text
Mid-level platform engineer, ~90 seconds.

  PRESENT - who I am and who I build for
    "I'm a platform engineer on a six-person team at a mid-sized software
     company. Our users are about forty product teams, and my area is the
     deploy path - how code gets from a merge to production."

  PAST - two threads, each with an outcome and a hook
    "The piece I'm proudest of is a shared pipeline that replaced nine bespoke
     ones. Thirty-one teams moved to it voluntarily over two quarters, and
     median time from commit to production went from about two days to under
     an hour. The hard part wasn't the pipeline - it was getting the last
     teams to adopt it, which taught me more about platform work than the
     build did.
     More recently I led moving our services off long-lived cloud keys to
     workload identity, so nothing in CI or the clusters stores a credential."

  FUTURE - why this role
    "I'd like to work on a platform at larger scale, and where there's a
     product role alongside the engineering - which is what drew me to this
     team. I'm particularly interested in the self-service infrastructure
     work mentioned in the job description."
  [stop]
```

```text
Career changer from application development, ~75 seconds.

  "I'm a backend engineer on a payments team. Over the last year I've ended
   up doing a lot of the work that helps other teams ship: I wrote the
   service template our department now uses for new services - eight teams
   have created services from it - and I set up the dashboards and alerts
   that come with it by default, because I kept seeing new services go live
   with no monitoring.
   That's the part of my job I enjoy most - building things other engineers
   use - so I'm looking to move into a platform team properly. This role
   appeals because you're early in building the golden path, and that's
   exactly the stage I've been working at, just informally."
```

```text
Common failures.

  the CV recital     "I started in 2016 at... then in 2018 I moved to..."
                     -> five minutes, no hooks, the interviewer has the CV
  the tool list      "I work with Kubernetes, Terraform, Argo CD, Helm..."
                     -> no users, no outcome, nothing to pull on
  the trailing end   "...so, yeah, that's kind of me, I guess."
                     -> end on the "why this role" line instead
```

## Interview tips

- Present, past, future, in ninety seconds to two minutes, then stop.
- Say who your users are in the first two sentences. It reframes everything you say next as platform work rather than tooling.
- Plant one or two hooks you have prepared to depth. The opening is the one moment in the interview where you choose the topic.
- Tailor the emphasis to the interviewer - recruiter, engineer, or hiring manager - without changing the facts.
- Rehearse the beats, not a script. Memorised answers sound memorised, especially on video.
- Keep the "why this role" part specific to the team or job description. A generic ending suggests you would say the same to anyone.
- If you are early in your career, use internal tools, templates, or automation you built for colleagues. The instinct to build for other engineers is what is being assessed.

---

[⬅ Back to Platform Engineering Interviews](./README.md) · [All topics](../README.md)
