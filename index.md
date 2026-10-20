# Spec Kit Workshop: Requirements-First Development with AI Agents

A 90-minute hands-on workshop. You will learn what Spec Kit is, how its
closed-loop, requirements-first workflow works from first principles, and
how to use it to build a small web application with an AI coding agent.

- **Audience**: experienced software engineers, proficient with agentic
  coding, new to Spec Kit.
- **Prerequisites**: a Linux host with git, snap, and the workshop CLI -
  the workshop runs in a container it builds and manages - plus a
  working agent setup on your host: OpenCode (your provider auth and
  model carry into the container), Antigravity agy (your Google credentials
  in `~/.gemini` carry into the container), or GitHub Copilot (log in inside the
  container on first use; its host credential store does not carry).
  The workshop script provisions uv and the agent integrations and creates
  the host-mounted petstore working tree. You install the `specify` CLI and
  create the virtual environment in the setup steps.
- **Format**: works self-paced (follow the numbered steps) or instructor-led.

## Introduction

Spec Kit is a process toolkit, not a framework. It changes how you work
with an AI coding agent from "describe a feature and hope" to "write a
spec, plan, break into tasks, analyze the artifacts for consistency,
implement, and verify the result against what you specified." The loop
is: **specify what to build, clarify ambiguity, plan how to build it,
break it into tasks, analyze the artifacts, implement, converge (check
the code against the spec and tasks, filling any gaps)**. Each step is a
command your agent runs; the output of each becomes the input of the
next. The result is a closed loop: nothing is "done" until the code
matches the spec and every task is built, so the agent (hopefully)
should not quietly skip requirements you stated.

Before the first feature you ratify the project **constitution**: the
principles every feature must honor. Plan, analyze, implement, and
converge all read it, so the loop has governance at a layer above
the feature artifacts.

```
specify -> clarify -> plan -> tasks -> analyze -> implement -> converge
  ^                                                                  |
  +------------------------------------------------------------------+
```

## Workshop outline

| # | Phase | What happens |
|---|---|---|
| 1 | [Setup](01-setup.md) | Launch the workshop container, install the CLI, create an empty project, ratify its constitution, confirm the commands are live |
| 2 | [Core concepts](02-core-concepts.md) | The constitution, the agentic loop, the artifacts, the commands, where validation fires |
| 3 | [The loop](03-the-loop.md) | You implement a basic pet store |
| 4 | [The refinement](04-the-refinement.md) | You implement order placement with a non-trivial requirement |
| 5 | [What's next](05-whats-next.md) | Extensions, presets, phasing for larger projects |

[06-reference.md](06-reference.md) is the cheat sheet students keep at hand.

## Learning objectives

By the end you will be able to:

1. Run the full Spec Kit loop: specify, clarify, plan, tasks, analyze,
   implement, converge.
2. Read and reason about the artifacts the loop produces (spec, plan,
   tasks).
3. Explain where and how "validation" actually fires (eg analyze's
   cross-artifact check and converge's check-the-code-against-the-spec
   step).
4. Establish a project constitution with `/speckit.constitution` and
   explain how plan, analyze, implement, and converge use it.
5. Know what to read next: extensions, presets, and how larger projects
   layer phased delivery.

## The project you will build: a pet store

A small REST API for a pet store: there's a pet catalog
(list, create, get, delete) and order placement. The feature
description you will work from includes a business rule, stated
as flat requirements: placing an order for a pet that is no longer
available **must fail**, and an order **may not** drive a pet's stock
below zero.
Your `~/petstore` working tree is mounted from `<clone>/petstore` on your
host, so you can follow along in your IDE.

## After the base workshop

- `06-reference.md`: the cheat sheet for future sessions.
- `05-whats-next.md`: a step-by-step phased-delivery lab (copy product
  artifacts, bootstrap the requirements extension, retrofit Phase 1
  specs, build R3 with the hooks), plus extensions, presets, and bundles.
  The reference companion is [`examples/petstore/`](examples/petstore/),
  and the full enforcement template is
  [`new-project-template/`](new-project-template/). For a new project,
  start with the template's
  [`docs/start-a-project.md`](new-project-template/docs/start-a-project.md)
  authoring guide and its starter requirement and roadmap files.
