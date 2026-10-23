# Spec Kit Workshop

This project contains a hands-on workshop that introduces Spec Kit and
illustrates its use by building a pet store application.

- [The 90-minute workshop](index.md) - this is a hands-on introduction:
  it starts with creating the project constitution, then the
  `specify -> clarify -> plan -> tasks -> analyze -> implement -> converge`
  loop, demoed on a pet store and practiced on an order-placement feature
  with a business rule which needs to be accounted for in the solution.

To run the workshop: `./scripts/workshop.sh`, then `workshop shell` - it
runs inside a container the workshop CLI builds ([setup](01-setup.md)).
The script creates `<clone>/petstore` on your host; the whole clone is
mounted at `/project`, so the generated project is `/project/petstore`
inside the container and visible in your IDE. It does not mount host agent
config; sign in inside the container on first use and the agent's SDK
persists the credential in the workshop.

---

## New project template

Spec Kit's core loop is excellent at taking one feature from idea to
working code. But it has no memory across features and cannot guarantee
that a spec contains the product requirement it claims to complete, or
that a completion claim is still current, or that the delivered interface
was actually tested.

The project template adds that missing layer. The core loop is unchanged.
The template adds the extra checks that ensure requirements are met
and interfaces are properly tested.

### What it adds

- **A product source of truth.** `REQUIREMENTS.md` states every requirement
  once with a stable ID. `ROADMAP.md` maps each requirement to the one
  feature that completes it, in dependency order.
- **Claims checked against the text.** Each completion claim must be
  backed by a curated phrase from its requirement that appears in the
  spec, so an ID in a table cannot claim content that was never written.
- **Freshness checked with digests.** Each completion claim records a
  SHA-256 of the requirement wording it was written against; when the
  wording changes, the verifier reports the claim as stale instead of
  silently passing.
- **Tests are required, including acceptance.** The tasks template and
  checklist require tests, failure paths, and an acceptance test through
  the real entry point; the acceptance-test command derives that test
  before implementation.
- **Enforcement where the work happens.** A requirements extension adds
  seven commands, two template overrides, and eight mandatory hooks around
  plan, tasks, analyze, implement, and converge. Workflow mode turns the
  coverage, plan, tasks, implement, diff, and final-tree checks into
  approve/reject gates.
- **A CI test backstop.** Plain pytest tests re-check the same claims in a
  bare checkout or CI, without the agent tooling installed, so drift fails
  the build even when no agent is in the loop.
- **A complete starting kit.** A two-part constitution, an authoring
  guide, starter requirements/roadmap files, a phrase extractor, and
  generated skills for OpenCode, Copilot, agy, and Claude Code.

### What it catches

| In a vanilla Spec Kit project | What this template adds |
| --- | --- |
| A spec claims a requirement but omits its content. | The requirement phrase check fails. |
| A requirement's wording changes after a spec was written. | The recorded digest goes stale and the verifier fails. |
| Test tasks are optional; the delivered interface is untested. | The tasks template requires tests and a real entry point acceptance test. |
| The author reviews their own diff. | A fresh context diff review runs after implement. |
| Analyze findings are reported but not fixed. | The remediation loop forces fixes and re-verification. |
| Enforcement lives in prose the agent can ignore. | Hooks, workflow gates, and pytest mirrors enforce it. |
| The roadmap marks a feature done without the code. | The verifier checks content; a human checks the code before status flips. |

### Use it

The workshop uses the template in [05 - What's Next](05-whats-next.md),
which bootstraps it into the petstore and retrofits the existing specs.
To seed a new project from scratch:

```bash
mkdir myproject && cd myproject
git init
specify init --here --non-interactive --integration <your-harness> --force
/path/to/speckit-workshop/new-project-template/bootstrap.sh "$(pwd)"
```

`<your-harness>` is an integration key from `specify integration list` (for
example `opencode`, `claude`, or `copilot`). See the
[template README](new-project-template/README.md) for prerequisites, the
fill-in checklist, and the full command surface, and
[`docs/start-a-project.md`](new-project-template/docs/start-a-project.md)
for the authoring walkthrough.
