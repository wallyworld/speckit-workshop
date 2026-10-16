# 05 - What's Next: Extensions, Presets, Phasing

## Extensions

Extensions add behaviors to Spec Kit on top of the vanilla loop you just
learned. They are optional; the core loop works without any.

- **How they load**: extensions are installed into the project with
  `specify extension add` and registered via `.specify/extensions.yml`
  (with a version/shape manifest). The CLI resolves them at runtime.
- **Upstream bundled**: the spec-kit upstream ships opt-in extensions.
  Two well-known examples are:
  - **bug** - a workflow for fixing bugs (assess, fix, test), rather
    than treating a bug as a feature.
  - **assess** - a workflow for gathering evidence about an idea before
    committing to a spec - it works even in a project with no source
    code yet.
  - Enable them by asking `specify` to add them (the official README has
    the exact command) - the mechanism is the same `extensions.yml`
    registration.
- **Community catalog**: a catalog of community-contributed extensions
  exists (for example TDD scaffolding, BDD scenario conversion,
  architecture governance checks). Browse it for shapes you can adopt or
  adapt.
- **Writing your own**: an extension is a directory with an
  `extension.yml` manifest declaring what it provides - commands
  (agent-facing markdown docs), templates (overriding the core spec and
  tasks templates), and hooks (mandatory checks injected around the core
  commands, registered into `.specify/extensions.yml` at install time) -
  plus any scripts the commands invoke. The requirements extension in
  [`new-project-template/`](new-project-template/) in this repository is
  the reference for the shape.

## Presets and bundles

At `specify init` you can select a **preset** - a packaged override of
the command, template, and script files, no new tooling. **Bundles** go
further: versioned stacks of extensions, presets, and workflows,
installed later with `specify bundle install` when a team wants one line
to standardize its spec template and guardrails across many repos. The
vanilla project you created during the workshop is the bare default.

## Phased delivery for larger projects

The workshop was deliberately **one feature, the full loop**. That is the
core model and it is the right way to learn Spec Kit.

Real-world products do not always map to "one feature done at a time."
Larger projects - a product with multiple related features, a release
train, a multi-team roadmap - commonly need to describe the *frontier* of
delivery: what the product is. The generic shape such projects add
on top of the vanilla core is:

1. **A requirements source.** A single document that states every
   requirement of the product, each with a stable ID, independently of
   any feature. ("The system must X.")
2. **A delivery roadmap.** A table mapping each requirement to a delivery
   phase and to a feature that realizes it, with a status per row.
3. **Per-feature claims.** Each feature spec declares which requirements
   it completes (and which it merely advances), referencing requirement
   IDs from the source.
4. **A verification step.** The roadmap row is only marked "done" when
   (a) the requirement's content is actually present in the spec, (b)
   the claim is fresh - not recorded against wording that has since
   changed - and (c) the code realizes it.

Upstream now documents a manual version of this layer - a roadmap
convention for oversized work, the [spec of
specs](https://github.github.io/spec-kit/concepts/spec-of-specs.html) -
with no tooling and no product-requirement semantics. The template
below implements that convention and adds both.

This is not more Spec Kit - it is the same loop, with an accounting layer
in front of it. Each requirement that the roadmap declares "done" has to
earn that status through a feature that went through the loop.

To see what this looks like for the pet store you built during the workshop, see
[`examples/petstore/`](examples/petstore/):
- [`REQUIREMENTS.md`](examples/petstore/REQUIREMENTS.md) groups the requirements
  into the backend API slices (Phase 1, what you just completed) and a full web
  user interface (Phase 2, for after the workshop).
- [`ROADMAP.md`](examples/petstore/ROADMAP.md) maps those requirements to delivery
  slices (`R1` catalog, `R2` orders, `R3` web UI).
- [`phrases.txt`](examples/petstore/phrases.txt) defines curated requirement phrases
  for deterministic traceability checking. In practice, you do not need to type
  these manually: an agent can generate them directly from `REQUIREMENTS.md` (or
  you can run the template's `extract-phrases.sh` script), and the verifier ensures
  every phrase matches verbatim.
- [`README.md`](examples/petstore/README.md) provides a step-by-step guide to
  **retrofit** these files into your `~/petstore` project, reconcile your existing
  Phase 1 sub-specs, and build the Phase 2 Web UI (`R3`).

The full tooling mechanics - requirements verifiers, moment-of-authoring hooks,
and review gates - ship ready-made in
[`new-project-template/`](new-project-template/) in this repository: it
seeds exactly this model - requirements source, roadmap map, requirement
phrases and requirement digests - together with tooling that verifies
each completion claim, and its README documents the formats and the
fill-in workflow.

## Reading list (all upstream)

- The [spec-kit README](https://github.com/github/spec-kit) (install
  instructions, preset/bundle reference, extension API).
- The spec-kit `/speckit.constitution` output as a model of writing
  project principles.
- The [community extension
  catalog](https://github.github.io/spec-kit/community/extensions.html)
  for workflow shapes.
