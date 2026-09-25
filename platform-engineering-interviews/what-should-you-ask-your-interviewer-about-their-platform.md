---
title: "What should you ask your interviewer about their platform?"
id: 251
category: "Platform Engineering Interviews"
difficulty: "Beginner"
tags:
  - platform-engineering
  - platform-engineering-interviews
  - interview-questions
---

# What should you ask your interviewer about their platform?

**Short answer:** Ask the questions whose answers tell you whether the platform is real: is adoption voluntary, does work arrive as tickets or as capabilities, what is the on-call load, what is the build-to-operate ratio, and who decides what gets built. Those five distinguish a platform team from an operations team with a new name - which is the single most important thing to establish, and asking them also demonstrates that you know the difference.

## Detail

**Your questions are part of the assessment.** Asking whether adoption is voluntary shows you know mandates produce shadow tooling. Asking about the build-to-operate ratio shows you know operational load crowds out capability work. Good questions do double duty here, which is why this round is worth preparing properly rather than improvising.

**The five that matter most, and what each answer tells you:**

| Question                                   | A good answer sounds like                       | A warning sounds like                  |
| ------------------------------------------ | ----------------------------------------------- | -------------------------------------- |
| Is adoption voluntary or mandated?         | "Voluntary, and we track it"                    | "Everyone has to use it"               |
| How does work reach the team?              | "A roadmap from user research and support data" | "A ticket queue"                       |
| What is the on-call load?                  | "Rotation of five, a couple of pages a shift"   | "It's quiet" with no numbers           |
| Build versus operate versus support split? | A number, roughly 50/25/25                      | "We're pretty busy"                    |
| Who decides what gets built?               | A named person doing product work               | "Whoever asks loudest" or "leadership" |

**Ask about the ticket queue specifically.** It is the clearest diagnostic. If most work arrives as requests for the team to perform, the role is operations regardless of the title, and you should know that before accepting. Phrasing it neutrally - "what proportion of your work is requests versus roadmap?" - gets a more honest answer than asking whether they are a service desk.

**Ask about their SLOs and whether they have an error budget policy.** A platform team with published capability SLOs and a signed error budget policy has an organisational immune system: it can decline work with authority. A team without one is subject to whatever is asked of it, and will be blamed for reliability it was never given time to build.

**Ask what they have deprecated.** A platform that has never removed anything is accumulating cost, and the answer tells you whether they can finish things. It is a surprisingly revealing question and few candidates ask it.

**Ask about the last incident where the platform was the cause.** How it was handled, whether the retrospective was blameless, and what changed. This tells you about the engineering culture more reliably than any question about culture.

**Ask what they decided not to build, and why.** A team that can answer has a real prioritisation process. A team that cannot is probably building whatever is requested, which is the same failure as the ticket queue in a different form.

**Ask about the developer experience they provide, in numbers.** Time to create a new service, time for a new engineer to reach production, lead time. If nobody knows, they are not measuring outcomes - which means you would be joining a team that cannot demonstrate its own value and will struggle to defend its funding.

**Ask how AI assistants and agents use the platform.** Coding assistants and autonomous agents are now platform consumers too - opening pull requests, calling platform APIs, sometimes through Model Context Protocol servers. Whether they act under their own scoped identities and the same policy as humans, or borrow a person's credentials, tells you how deliberately the team is handling the newest class of user.

**Tailor by interviewer.** The hiring manager can answer about roadmap, staffing, and how success is judged. An engineer on the team is the right person to ask about on-call load, the worst part of the job, and what they would fix. Ask an engineer what they would change if they could change one thing - it is the most candid answer you will get in the whole loop.

**Ask about your own first ninety days.** What would success look like, and what is already waiting for you. A clear answer suggests a team that has thought about onboarding; a vague one suggests you will be absorbed into whatever is on fire.

## Example

```text
Tailored by who you are speaking to.

  TO THE HIRING MANAGER
    "Is adoption of the platform voluntary, or mandated? How do you track it?"
    "What proportion of the team's work arrives as requests versus roadmap?"
    "Who decides what gets built - is there someone doing the product role?"
    "Do you have SLOs on platform capabilities, and an error budget policy?"
    "What have you deprecated and removed in the last year?"
    "What did you decide NOT to build, and why?"
    "How do AI coding assistants and agents use the platform, and under what identity?"
    "What would success look like for me in ninety days?"

  TO AN ENGINEER ON THE TEAM  (the most candid answers in the loop)
    "What is the on-call rotation, and how many pages in a typical shift?"
    "Roughly how does your time split between building, operating, and support?"
    "What is the worst part of the job?"
    "If you could change one thing about the platform, what would it be?"
    "Tell me about the last incident where the platform was the cause - how was
     the retrospective?"
    "How many clusters and runtimes do you support?"   <-- proxy for operational load

  TO A STREAM-ALIGNED ENGINEER, if you get the chance - the best source
    "Would you use the platform if you did not have to?"
    "What do you still do by hand?"
    "How long does it take you to get a new service into production?"
```

```text
Reading the answers.

  "Adoption is mandated - everyone has to use it."
  -> the team has no feedback signal, and there is probably shadow tooling they
     do not know about. Ask whether they track voluntary usage of individual
     capabilities. Not disqualifying; it is a thing you would need to change.

  "Most of our work comes in as tickets."
  -> this is an operations role with a platform title. Perfectly fine work, but
     know it before accepting, and ask whether there is appetite to change it.

  "On-call? It's pretty quiet."  ...with no numbers.
  -> either genuinely quiet or nobody is measuring. Ask for pages per shift and
     out-of-hours pages per week. Vagueness here is the answer.

  "We support nine clusters, three clouds, and four runtimes."  ...with five engineers.
  -> the operate share of their time is very high, and little gets built. Ask
     about the build/operate split and watch the reaction.

  "We haven't deprecated anything yet."
  -> accumulating cost, and possibly cannot finish things. Ask what they would
     remove if they could.

  "The last platform incident was a policy we rolled out without an audit period.
   We wrote it up, changed the release process to require a violation count, and
   added an SLO on the deploy capability because nothing alerted for 40 minutes."
  -> excellent answer. Blameless, specific, and it produced structural change.
     This is a team that learns.

  "Nobody has measured time to create a service."
  -> they cannot demonstrate their own value, which means their funding is
     vulnerable and your work will be hard to defend.
```

## Interview tips

- Prepare these properly; they are part of the assessment. Asking whether adoption is voluntary signals that you know mandates produce shadow tooling.
- The five diagnostics - voluntary adoption, how work arrives, on-call load, the build/operate split, and who decides - are the ones that distinguish a platform team from a renamed operations team.
- Phrase the ticket-queue question neutrally as a proportion. It gets a far more honest answer than asking whether they are a service desk.
- Asking about SLOs and an error budget policy shows you understand that a platform team needs a mechanism to decline work.
- "What have you deprecated?" and "what did you decide not to build?" are two questions almost nobody asks and both are highly revealing.
- Ask an engineer what they would change if they could change one thing. It is the most candid answer available in the whole loop.
- Ask about the last incident the platform caused and how the retrospective went. It tells you more about culture than any direct question about culture.
- If a number does not exist - on-call pages, time to create a service - treat the absence as the answer.

---

[⬅ Back to Platform Engineering Interviews](./README.md) · [All topics](../README.md)
