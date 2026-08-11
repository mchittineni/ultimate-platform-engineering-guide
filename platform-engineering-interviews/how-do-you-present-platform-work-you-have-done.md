---
title: "How do you present platform work you have done?"
id: 132
category: "Platform Engineering Interviews"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - platform-engineering-interviews
  - interview-questions
---

# How do you present platform work you have done?

**Short answer:** Lead with the problem and who had it, state what you changed and what happened to a number, then explain one interesting decision and its trade-off - and be specific about what you personally did versus what the team did. The failure that costs candidates the round is describing the tools they used rather than the problem they solved, because a tool list is indistinguishable from having read about the tools.

## Detail

**Structure it as problem, users, change, outcome, decision.** In that order. The problem and its users establish that the work was needed; the outcome establishes that it worked; the decision is where the interviewer learns how you think, which is the actual point of the question.

**Name the users and their pain.** "Forty teams, and provisioning a database took three and a half days, almost all of it waiting for our review" is a problem. "We built a self-service platform" is a description of an artefact. The pain is what makes the rest meaningful, and platform interviewers are specifically listening for whether you know who your users were.

**Have numbers, and be honest about their quality.** Before and after on something that matters - lead time, provisioning time, adoption, support tickets, cost, onboarding time. If you do not have exact figures, an honest approximation with its basis is far better than none: "we did not baseline properly, so this is from the ticket queue and my memory - roughly three days to under ten minutes." Interviewers respect the caveat and distrust suspiciously precise claims.

**Pick a decision with a real trade-off.** The most revealing part of your story is a choice where the alternative was defensible. Crossplane over Terraform and what you gave up. Namespaces over clusters and where it strained. Buying rather than building. Not building a portal. Explaining what you rejected and why demonstrates judgement in a way a successful outcome alone does not.

**Say what went wrong and what you would change.** Every real project has something. A candidate who presents an unblemished success either has not reflected or is not being straight, and either reading is worse than the flaw itself. The strongest version names something specific and says what you would do differently.

**Be precise about attribution.** "I designed the interface and wrote the controller; a colleague did the observability integration; the migration was the whole team" is credible and complete. Overclaiming is easily detected by follow-up questions, and underclaiming leaves the interviewer unable to assess you. Use "I" for what you did and "we" for what the team did, deliberately.

**Prepare for the depth probe.** Interviewers will pick one detail and go three levels down. If you say you used a conversion webhook, expect to be asked how the two versions were mapped and what happened to a field that existed in one and not the other. Prepare two or three projects properly rather than five superficially.

**Include the adoption story.** For platform work specifically, how you got teams to use it is at least as interesting as how you built it. Voluntary adoption, how you got the first team, what you did about the teams who declined - this is the part most candidates omit and it is often what the interviewer most wants.

**Keep the opening tight.** Two or three minutes for the whole arc, then let the interviewer pull on whichever thread they want. A ten-minute uninterrupted narration uses the round's time on your priorities rather than theirs, and it prevents the conversation that actually assesses you.

## Example

```text
The same project, presented two ways.

WEAK - a tool list. Indistinguishable from having read about the tools.
  "We built an internal developer platform using Kubernetes, Crossplane, Argo CD,
   Backstage, and Kyverno. I worked on the Crossplane compositions and helped
   set up Argo CD. We had about 40 teams using it and it worked well."
  -> no problem, no users, no number, no decision, no trade-off, and no way to
     tell what this person actually did.

STRONG - problem, users, change, outcome, decision. ~2.5 minutes.
  PROBLEM AND USERS
  "Forty product teams, and getting a database took a median of three and a half
   days. Almost all of that was waiting for my team to review a Terraform pull
   request. We were five people and the queue was the bottleneck for everyone.
   We were also getting fourteen support tickets a month that were just 'my
   Terraform plan looks wrong'."

  WHAT I CHANGED
  "I designed a claim-based interface - four fields: size, backup cadence,
   point-in-time recovery, and where to write the connection secret. Teams got
   RBAC on that resource and no AWS permissions at all. I wrote the Crossplane
   compositions that expand it, with encryption, private subnets, tagging, and
   backup policy applied unconditionally - no field exposes them, so a
   non-compliant database is not expressible."

  OUTCOME, with honest provenance
  "Median time to a database went from three and a half days to about eight
   minutes. Those fourteen monthly tickets went to roughly one. I should say we
   did not baseline properly at the start, so the three-and-a-half-day figure is
   from the ticket queue rather than instrumentation."

  THE DECISION WITH A REAL TRADE-OFF
  "The interesting choice was Crossplane over keeping Terraform with PR
   automation. What we gained was continuous reconciliation - console drift got
   corrected instead of sitting until someone ran a plan - and a self-service
   interface with RBAC and admission control we already had. What we gave up was
   the reviewable plan, which is genuinely valuable. There is no first-class
   'what will this change' for Crossplane, so we compensated with a staging
   environment and admission policy on the dangerous fields. If the estate had
   been mostly stateful infrastructure changing rarely, I would probably have
   stayed with Terraform."

  WHAT WENT WRONG
  "We shipped it with the default deletion policy. Two weeks in, someone deleted
   a namespace in staging and it destroyed the database. Staging, so it cost us a
   day. If it had been production it would have been a serious incident. We moved
   everything stateful to orphan-on-delete and added admission policy requiring
   an explicit annotation. I should have thought about deletion at the same time
   as creation - that is the thing I would change."

  ATTRIBUTION, unprompted
  "To be clear on scope: I designed the interface and wrote the compositions. A
   colleague built the observability integration. The migration of forty teams was
   the whole team over about five months."
```

```text
The depth probe - be ready to go three levels down on anything you said.

  interviewer  "you said admission policy on dangerous fields. Which fields, and
                what does the policy do?"
  you          "size: large needs a budget-approval annotation, because the cost
                step is significant. And deletion of any production claim needs
                an annotation matching the resource's own name - so it cannot be
                produced by a namespace deletion or a Git prune."

  interviewer  "what happens if the platform's controller is down?"
  you          "no new databases can be provisioned; existing ones are completely
                unaffected because the controller is not in any request path.
                Control-plane failure should stop change, not stop serving."

  interviewer  "how did you get the first team to use it?"
  you          "picked the team whose pain it removed rather than the keenest one.
                Paired with them for three days, fixed nine rough edges that week,
                then had THEM write the internal post. Five teams asked to be
                next, unprompted. That write-up was the highest-return thing in
                the whole project."

  -> prepare two or three projects to this depth rather than five superficially.
```

## Interview tips

- Use the order: problem, users, change, outcome, decision. Leading with tools is the single most common and most costly mistake in this round.
- Name the users and quantify their pain. "Forty teams waiting three and a half days" does work that "we built a platform" cannot.
- Have numbers and state their provenance. An honest approximation with its basis beats both no number and a suspiciously precise one.
- Choose a decision where the alternative was genuinely defensible, and explain what you gave up. That is where the interviewer learns how you think.
- Volunteer what went wrong. The deletion-policy example is the kind of specific, technical, consequential mistake that improves an answer rather than damaging it.
- Be precise about attribution without being asked - "I" for your work, "we" for the team's. Overclaiming is easily unpicked by follow-ups.
- Include the adoption story; for platform roles it is often what the interviewer most wants and what candidates most often omit.
- Keep the opening to two or three minutes and then let them pull threads. Prepare two or three projects to real depth rather than five superficially.

---

[⬅ Back to Platform Engineering Interviews](./README.md) · [All topics](../README.md)
