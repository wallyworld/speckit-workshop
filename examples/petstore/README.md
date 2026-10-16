# Pet Store Phased Delivery Example

This directory provides a concrete example of the **phased delivery** model
described in [05 - What's Next](../../05-whats-next.md).

## How This Maps to the Workshop

- **Phase 1 (Backend API)**:
  - **R1** ([`CAT-1` through `CAT-4`](REQUIREMENTS.md)): Completed in
    [03 - The Loop](../../03-the-loop.md).
  - **R2** ([`ORD-1` through `ORD-4`](REQUIREMENTS.md)): Completed in
    [04 - The Refinement](../../04-the-refinement.md).
- **Phase 2 (Web UI)**:
  - **R3** ([`UI-1` through `UI-5`](REQUIREMENTS.md)): A follow-up feature
    slice to build after the workshop.


---

## Retrofitting to Your Workshop Project

If you completed exercises 01 through 04 in your container (`~/petstore`), you
already have a working Phase 1 backend. You can retrofit `REQUIREMENTS.md` and
`ROADMAP.md` directly into your project to establish the multi-phase accounting
layer and build Phase 2.

### Step 1: Copy the requirements and roadmap into your project

Inside your workshop container (`workshop shell`):

```bash
cd ~/petstore
cp /project/examples/petstore/REQUIREMENTS.md .
cp /project/examples/petstore/ROADMAP.md .
```

### Step 2: Reconcile existing sub-spec paths in `ROADMAP.md`

In earlier exercises, Spec Kit generated feature directories whose slugs were
derived dynamically from the agent's prompt (for example `specs/001-pet-crud/` or
maybe `specs/001-pet-catalog/`; name depends on the agent's decision at the time).

Check your actual directory names:

```bash
ls specs/
```

Open `ROADMAP.md` in your editor and verify that the `Sub-spec` column for `R1`
and `R2` matches your directory names. Both slices are already `done`:

```markdown
| ID | Sub-feature | Intent | Scope boundary | Depends on | Status | Completes (RQ) | Advances (RQ) | Sub-spec |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R1 | Pet catalog API | Fast, minimal CRUD API for pets and inventory stock. | Storage and API only; no order processing. | - | done | CAT-1, CAT-2, CAT-3, CAT-4 | - | [`001-pet-catalog`](specs/001-pet-catalog/) |
| R2 | Order placement API | Safe order placement and cancellation with inventory guards. | Backend order endpoints; no frontend UI. | R1 | done | ORD-1, ORD-2, ORD-3, ORD-4 | - | [`002-order-placement`](specs/002-order-placement/) |
| R3 | Pet store Web UI | Interactive browser frontend connecting catalog and orders. | Client frontend served by FastAPI; uses existing R1/R2 API; no external frontend build tools. | R1, R2 | planned | UI-1, UI-2, UI-3, UI-4, UI-5 | - | [`003-web-ui`](specs/003-web-ui/) |
```

---

### Step 3 (optional): Bootstrap the traceability tooling first

`REQUIREMENTS.md` and `ROADMAP.md` only do work once the traceability
tooling rides on top of them. If you want the `R3` slice you are about to
build to be enforced by the verifier, bootstrap the tooling **now, before
authoring the spec**: the extension supplies the spec template that carries
the Requirements Coverage table and the requirement digests the verifier
reads, so a spec authored before bootstrap will not have them.

```bash
/project/new-project-template/bootstrap.sh ~/petstore
cp /project/examples/petstore/phrases.txt ~/petstore/extensions/requirements/data/phrases.txt
```

(Bootstrap prints a fill-in checklist; here the copied `REQUIREMENTS.md`,
`ROADMAP.md`, and `phrases.txt` already resolve the requirement-facing
items. To draft phrases instead of copying the curated file, see the note
under "Verify Requirement Traceability" below.)

Bootstrap also installs the **enforcement layer**, so the R3 build below
runs under it: mandatory checklists fire around specify, plan, tasks,
implement, analyze, and converge; the `after_implement` hook commissions
an independent fresh-context review of the implementation diff
(`/speckit-requirements-diff-review`) before the agent reports the work
done; and in workflow mode the same checks appear as approve/reject
review gates (`review-coverage`, `review-plan-checklist`, `review-tasks`,
`review-implement-checklist`, `review-diff`, `review-final-tree`). The
[template README](../../new-project-template/README.md) documents each
check.

If you skip this step, the Phase 2 build below still works; only the final
verification step is unavailable.

---

## Building Phase 2: Slice `R3` (Web UI)

With the requirements and roadmap in place, you can now drive slice `R3` through
the Spec Kit loop. Because the requirements and architecture constraints are
already documented in `REQUIREMENTS.md` and `ROADMAP.md`, you do not need to
copy-paste verbose prompts - the agent reads the context directly from the
repository:

> **Command form.** Commands below use OpenCode's dot form; with agy or
> Copilot use the hyphenated form (`/speckit-specify`, ...).

### 1. Specify

Run in your agent:

```text
/speckit.specify Implement slice R3 from ROADMAP.md
```

The agent reads `ROADMAP.md` and `REQUIREMENTS.md` directly from disk and drafts
`specs/003-<slug>/spec.md` with requirements `UI-1` through `UI-5`.

### 2. Clarify (optional)

```text
/speckit.clarify
```

Address any design questions (e.g. styling preferences or component layout).

### 3. Plan

```text
/speckit.plan
```

> **Why no prompt text here?**
> In exercises 03 and 04, you typed tech-stack instructions inline into
> `/speckit.plan` because there was no requirements document or existing code.
> In phased delivery, the architecture constraints (FastAPI-served single-page app,
> no node runtime) are already codified in `REQUIREMENTS.md` (`UI-5`), and the existing
> backend is already implemented in `petstore_app.py`. The agent inspects both
> and designs `plan.md` automatically.

### 4. Tasks

```text
/speckit.tasks
```

### 5. Implement

```text
/speckit.implement
```

The agent writes the HTML/JS/CSS frontend, wires up the FastAPI static route or
index handler, and verifies tests. With the tooling bootstrapped, the
`before_implement` checklist applies to the changes being written, and the
`after_implement` hook then commissions an independent review of the diff
before the work is reported done.

### 6. Converge

```text
/speckit.converge
```

Verify that all functional requirements in `UI-1` through `UI-5` are implemented
and converged.

### 7. Close the Loop in `ROADMAP.md`

Update `ROADMAP.md` row `R3`:
- Change `Status` from `planned` to `done`.
- Update the `Sub-spec` column to link to your generated `specs/003-...` directory.

---

## Testing Your New Web UI

Start your FastAPI application:

```bash
uv run uvicorn petstore_app:app --reload --host 0.0.0.0
```

From your host browser, navigate to your workshop host address (obtained from
`workshop info` on your host, e.g.
`http://speckit-ws.speckit-workshop.wp:8000/`).

You can now interact with the live UI:
- View the catalog of pets with live availability badges (`UI-1`).
- Add pets and see the list update dynamically (`UI-2`).
- Place an order and watch stock decrement, with order buttons disabling at 0 (`UI-3`).
- View open orders and cancel them to restore inventory (`UI-4`).

---

## Verify Requirement Traceability (if you bootstrapped the tooling)

If you bootstrapped the tooling in Step 3 (before authoring the `R3`
spec), confirm that the spec satisfies the requirements it claims to
complete:

```bash
bash ~/petstore/extensions/requirements/scripts/bash/verify-traceability.sh ~/petstore/specs/003-*/spec.md
```

The verifier confirms that the spec body contains verbatim requirement
phrases from `REQUIREMENTS.md` and that requirement digests match.

To draft the phrases instead of copying the curated file, run (from
`~/petstore`):

```bash
bash extensions/requirements/scripts/bash/extract-phrases.sh REQUIREMENTS.md -o extensions/requirements/data/phrases.txt
```

Generated candidates are guaranteed verbatim but not guaranteed
distinctive; review them and prefer wording unique to each requirement.
The automated enforcement layer is described in
[`new-project-template/`](../../new-project-template/).
