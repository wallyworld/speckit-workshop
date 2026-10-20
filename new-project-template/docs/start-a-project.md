# Start a Multi-Phase Project

This guide takes a freshly seeded project from a product idea to its first
delivery slice, then shows how to add later phases. It is the authoring
counterpart to the template README's conventions section: the README states
the formats the tooling expects; this guide is the procedure for producing
them.

The guide assumes `bootstrap.sh` has already run in your project. If it has
not, start with the template README's "Seed a project" instructions, then
return here.

> **Command form.** This guide shows OpenCode's dot form for both core and
> extension commands (`/speckit.specify`,
> `/speckit.requirements.prepare`). With agy or Copilot, use the hyphenated
> skill form (`/speckit-specify`, `/speckit-requirements-prepare`).

## The model TL;DR

Four artifacts drive a multi-phase delivery:

1. `REQUIREMENTS.md` states every product requirement once, with a stable
   ID, independently of any feature.
2. `ROADMAP.md` maps every requirement to the one feature that Completes
   it. An earlier feature may Advance a requirement without completing it.
3. Each feature spec claims the requirements it Completes and the ones it
   only Advances.
4. The tooling verifies that the spec contains the claimed requirement
   wording, that the recorded digest still matches the current wording, and
   that the code realizes it.

Delivery is one feature slice at a time. The roadmap is the order. Do not
try to specify the whole product in one feature.

## 1. Define the first slice

Write down, in a scratch note or at the top of `REQUIREMENTS.md`:

- the product goal: what user problem the product solves;
- the users and their entry point: web page, CLI, API, device, or file;
- the first slice: the smallest end-to-end outcome that is useful on its
  own;
- what is explicitly out of scope for the first slice;
- the later phases you can already foresee.

A good first slice has a real entry point and an observable result. "Set up
the database" is not a slice. "A user can add a note and see it in the
list" is a slice.

Keep later phases coarse. You will refine each one when its turn comes.

## 2. Author `REQUIREMENTS.md`

Copy the starter, then replace it with your product:

```bash
cp docs/REQUIREMENTS.md.example REQUIREMENTS.md
```

The file is Markdown. The tooling parses requirement bullets; section
headings are for humans and are not parsed. Keep the grammar exact:

```markdown
### Phase 1: Notes

- **NOTE-1**: The system MUST let a user create a note with a title and a
  body.
- **NOTE-2**: The system MUST list notes newest first.

### Phase 2: Sharing

- **SHARE-1**: The system MUST let the owner share a note read-only with
  another named user.
```

Rules that matter to the tooling and to review:

- **Bullet grammar.** A requirement starts at column zero with
  `- **PREFIX-N**:`, where `PREFIX` is uppercase letters and `N` is a
  positive integer. A lowercase letter suffix is allowed after `N` when a
  requirement is split, for example `NOTE-2a`.
- **Continuation lines are indented.** The parser joins indented lines to
  the requirement. A blank line or an unindented line ends the requirement.
- **IDs are stable.** Never renumber or reuse an ID. IDs are global across
  the file, so use a different prefix for each section. Section scoping
  keeps IDs readable; it does not make duplicate IDs legal.
- **One requirement per bullet.** Do not hide two independent MUSTs in one
  bullet. Split them and use a letter-suffixed child if the original is
  already referenced.
- **State observable behaviour.** A requirement should describe what a user
  or caller can observe, not which table, function, or framework you will
  use. State a technology only when it is a real product constraint.
- **Use MUST deliberately.** The phrase extractor reads the MUST clause to
  propose curated phrases. A requirement with no MUST still needs a phrase
  entry, but the wording is harder to categorize.
- **No em dashes.** Use a hyphen instead. The style gate enforces this.
- **Keep placeholders out of the final file.** The starter uses fill-in
  markers so an unresolved copy fails the gate. Replace every marker before
  running the first feature.

A requirement is ready when a test could decide whether it is satisfied and
a reviewer could decide whether the code silently expanded its scope.

## 3. Author `ROADMAP.md`

Copy the starter, then replace the example rows:

```bash
cp docs/ROADMAP.md.example ROADMAP.md
```

The table header is fixed. It must have exactly these nine columns, in this
order:

```markdown
| ID | Sub-feature | Intent | Scope boundary | Depends on | Status | Completes (RQ) | Advances (RQ) | Sub-spec |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
```

Rows are one feature slice each. Keep each row on one line; the parser does
not support wrapped table rows.

- **ID.** `R1`, `R2`, and so on. Never rename a delivered row. Order rows by
  delivery order.
- **Sub-feature.** A short name for the slice.
- **Intent.** The outcome the slice delivers, in one sentence.
- **Scope boundary.** What the slice deliberately does not do.
- **Depends on.** Comma-separated roadmap IDs, or `-`. Every dependency must
  exist and must be `done` before this row can be prepared. The first row
  has no dependencies.
- **Status.** `planned` until the slice is delivered. Set it to `done` only
  after the acceptance gate passes. The prepare command treats any status
  other than `done` as incomplete.
- **Completes (RQ).** The requirement IDs this slice fully delivers. Every
  requirement in `REQUIREMENTS.md` must appear in exactly one `Completes`
  cell across the whole roadmap. This is the sole requirement-to-feature
  mapping.
- **Advances (RQ).** Requirements this slice only lays groundwork for. They
  still need a later `Completes` row. Do not record an Advances-only
  requirement as complete.
- **Sub-spec.** The generated `specs/NNN-<slug>/` directory for a delivered
  slice. Use `-` until the spec exists, then fill it in.

An example with two slices:

```markdown
| ID | Sub-feature | Intent | Scope boundary | Depends on | Status | Completes (RQ) | Advances (RQ) | Sub-spec |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R1 | Notes CRUD | Users create and list notes. | No sharing, search, or editing. | - | planned | NOTE-1, NOTE-2 | - | - |
| R2 | Note sharing | Owners share a note read-only. | No collaborative editing or permissions UI. | R1 | planned | SHARE-1 | - | - |
```

Before moving on, read the two files together and check the mapping in both
directions:

- every requirement has exactly one `Completes` owner;
- every `Completes` and `Advances` ID exists in `REQUIREMENTS.md`;
- no row depends on itself or on a row that is not earlier in the order;
- the first row has no dependencies.

## 4. Generate `requirement-phrases.txt`

Phrases tie a completion claim to the requirement's own wording. Generate
candidates from the requirements file:

```bash
bash extensions/requirements/scripts/bash/extract-phrases.sh REQUIREMENTS.md -o requirement-phrases.txt
```

The extractor guarantees that every phrase it writes is verbatim requirement
wording. It does not guarantee that the phrase is distinctive. Review the
file:

- each requirement ID has one entry;
- each phrase is specific enough that a spec could not satisfy it by
  accident;
- no entry cites an ID that is absent from `REQUIREMENTS.md`;
- the file contains no stale phrases from deleted or renamed requirements.

The verifier fails closed on a missing entry, a non-verbatim phrase, or an
entry for an unknown ID. A generic phrase such as "list notes" is verbatim
but weak; replace it with wording unique to the requirement.

## 5. Validate before the first feature

Run the project gate:

```bash
make install
make test
```

`make test` also checks the other seeded skeletons, so resolve the remaining
fill-in items from the bootstrap checklist (AGENTS.md, CONTRIBUTING.md,
agent-instructions.md, docs/implementation-mechanics.md, the constitution,
and the extension repository URL) before expecting a clean run.

Some checks activate only after the first spec exists. The traceability
suite still validates the phrases table against `REQUIREMENTS.md` as soon as
the requirements file declares IDs.

Then validate the first roadmap row end to end:

```text
/speckit.requirements.prepare R1
```

The command checks that `R1` exists, that its dependencies are `done`, and
that every requirement ID in its Completes and Advances cells exists. It
prints a read-only brief with the canonical requirement text and digests.
Review it before running the emitted specify command.

If prepare reports a dependency that is not `done`, either deliver the
dependency first or correct the `Depends on` cell. Dependencies are real
ordering constraints, not documentation.

## 6. Deliver the slice and close the row

Run the core specify command emitted by the brief exactly once, then the
rest of the loop. A second specify creates another numbered spec
directory, so a roadmap row always has one spec:

```text
/speckit.clarify
/speckit.plan
/speckit.tasks
/speckit.requirements.acceptance-test R1
/speckit.analyze
/speckit.implement
/speckit.converge
```

If the slice is a browser UI, install the browser driver in the project
environment before generating the test and use the browser the environment
provides. In the workshop container, install Chrome on demand from a host
terminal in the clone with `workshop run --uid 0 -- install-browser`, then
run `uv pip install pytest-playwright`; do not run `playwright install`.

After the acceptance gate passes:

1. update the `R1` row in `ROADMAP.md`:
   - set `Status` to `done`;
   - set `Sub-spec` to the generated directory, for example
     `specs/001-notes-crud/`;
2. rerun `make test`;
3. commit the requirements, roadmap, phrases, spec, and code together.

A roadmap row is a claim. Do not mark it `done` while a claimed requirement
is missing from the spec, stale, or unimplemented.

## 7. Add the next phase

When you start a new phase:

1. Append a new section to `REQUIREMENTS.md` with a new prefix. Do not
   renumber existing requirements and do not reuse a retired ID.
2. Append one or more roadmap rows. Set `Depends on` to the delivered rows
   the new slice needs, and leave the status `planned`.
3. Map the new requirements. Every new requirement needs exactly one
   `Completes` owner. Use `Advances` only for groundwork that a later row
   will complete.
4. Regenerate `requirement-phrases.txt` and review the new entries.
5. Run `make test` and `/speckit.requirements.prepare` for the next row,
   for example `/speckit.requirements.prepare R2`.
6. Deliver the slice and close the row as in step 6.

If a requirement's wording changes after a spec recorded it, the recorded
digest becomes stale. Regenerate the phrases and update the spec through
the prepare brief. Do not silently edit the requirement text and leave the
old digest in place.

If a requirement is split, keep the original ID and add letter-suffixed
children beneath it, for example `NOTE-2` and `NOTE-2a`. Map each child to
the feature that completes it; a child that is only groundwork goes under
`Advances` until its Completes row exists.

## Definition of ready

A first phase is ready to specify when all of these are true:

- the product goal, users, entry point, and out-of-scope boundary are
  written down;
- the first slice is an end-to-end outcome, not an internal setup step;
- every requirement is one observable MUST with a stable ID;
- every requirement has exactly one `Completes` owner in the roadmap;
- every roadmap dependency exists and is ordered before the row;
- every requirement ID has a reviewed, distinctive phrase;
- `make test` passes once the bootstrap fill-in checklist is complete,
  and `/speckit.requirements.prepare R1` emits a brief.

## Common mistakes

- **Leading spaces before a requirement bullet.** The parser only matches a
  bullet at column zero.
- **A compound requirement.** "Create a note and share it" is two
  requirements; split it.
- **An orphan requirement.** It has a phrase but no roadmap `Completes` row,
  so no feature will ever deliver it.
- **Two owners.** Two roadmap rows claim the same requirement. Exactly one
  feature completes it.
- **Advances mistaken for completion.** A foundation row advances a
  requirement; it does not complete it.
- **An unmet dependency.** The prepare command refuses a row whose
  predecessor is not `done`.
- **A wrapped roadmap row.** Keep each row on one line.
- **Stale wording.** Requirement text changed after a spec recorded it.
  Regenerate phrases and refresh the digest through the brief.
- **Copying the petstore sample as your product.** The petstore artifacts
  are a worked reference. Start from the starter files in `docs/`.
