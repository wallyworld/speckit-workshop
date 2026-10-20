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

The workshop uses this template in its final phased-delivery stage:
[05 - What's Next](05-whats-next.md) bootstraps it into the petstore and
retrofits the existing specs. The same template seeds a new project from
scratch.

Spec Kit's core loop works one feature at a time. The template adds the
product-level accounting layer above that loop, so a multi-feature product
keeps its requirements, delivery order, and completion claims consistent:

- **Product-level requirements** - `REQUIREMENTS.md` states every requirement
  once with a stable ID.
- **Delivery roadmap** - `ROADMAP.md` maps every requirement to the one
  feature that completes it, in dependency order.
- **Content and freshness checks** - requirement phrases prove a spec
  contains the claimed requirement; SHA-256 digests flag claims written
  against older wording.
- **Enforcement at authoring time** - a requirements extension adds commands,
  hooks, workflow gates, and spec/tasks template overrides.
- **Mirror tests** - plain pytest checks re-verify the same claims in a bare
  checkout or CI, without the agent tooling installed.
- **A full starting kit** - a two-part constitution, an authoring guide,
  starter requirements/roadmap files, generated skills, and wiring for
  OpenCode, Copilot, agy, and Claude Code.

To seed a new project:

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
