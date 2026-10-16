"""Enforcement-chain mirror tests: registration, surfacing, templates, gates.

AGENTS.md's enforcement map claims that the enforcement checks fire
automatically: the extension's hooks are registered in
``.specify/extensions.yml``, the vendored skills surface them at the
command lifecycle points, the workflow overlay mirrors them as gates, and
the extension provides the project's spec and tasks templates. A
spec-kit upgrade can wipe the hook registrations silently (the installer
purges hooks a reinstalled manifest does not declare) and without a mirror test
every gate stays green while the enforcement checks stop firing. This
module re-checks each link so any
future break - a wiped registration, a re-vendored skill that stops
surfacing hooks, a resolver change that drops the project templates, an
overlay that stops composing, a checklist summary that stops carrying
the checklist's rules - fails ``make test``.

Portable by design: a mirror test skips with a stated reason when its surface
does not exist in this project (for example a repository that has not
vendored the core skills). A surface integral to an adopted requirements
extension - its manifest, its tracked hook registration, the workflow
overlay its commands claim to fire as gates, the AGENTS.md destination
the checklists point at - fails instead of skipping when missing: the
module travels to a non-adopting repository without false failures,
and a broken chain in an adopting repository never slips past as a
skip.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
EXTENSIONS_YML = ROOT / ".specify" / "extensions.yml"
SKILLS_DIR = ROOT / ".github" / "skills"
EXTENSION_SOURCE = ROOT / "extensions" / "requirements"
MANIFEST = EXTENSION_SOURCE / "extension.yml"
GATES_YML = ROOT / ".specify" / "workflows" / "overlays" / "speckit" / "review-gates.yml"
RESOLVE_TEMPLATE = ROOT / ".specify" / "scripts" / "bash" / "resolve-template.sh"
REINSTALL = "specify extension add --dev --force extensions/requirements"

# The extension's mandatory hook registrations, as
# (event, command, optional, enabled, condition). Declared in
# extensions/requirements/extension.yml and registered into
# .specify/extensions.yml at install time; the skills read the registrations
# from .specify/extensions.yml to fire the enforcement checks. The vendored
# skills skip hooks with enabled: false and any hook with a non-empty
# condition, so the test asserts the full firing-relevant shape: a disabled or
# conditioned registration is a silent no-fire, not just a missing one.
EXPECTED_HOOKS = {
    ("before_plan", "speckit.requirements.plan-checklist", False, True, None),
    ("before_tasks", "speckit.requirements.tasks-checklist", False, True, None),
    ("before_implement", "speckit.requirements.tasks-checklist", False, True, None),
    ("after_implement", "speckit.requirements.diff-review", False, True, None),
    ("before_analyze", "speckit.requirements.verify", False, True, None),
    ("after_analyze", "speckit.requirements.remediation-loop", False, True, None),
    ("before_converge", "speckit.requirements.verify", False, True, None),
    ("before_converge", "speckit.requirements.tasks-checklist", False, True, None),
}

# The hooks the core commands must still surface, by core-command base name.
# The installer writes the command into whichever integration was chosen at
# `specify init`, so the surface differs per tool (opencode installs
# `.opencode/commands/speckit.<name>.md`; copilot, claude, and agy install
# `<tool>/skills/speckit-<name>/SKILL.md`). If a future re-vendor drops or
# renames a hook section, the enforcement checks stop being surfaced even
# though the registrations are intact.
EXPECTED_HOOK_SECTIONS = {
    "plan": ("hooks.before_plan",),
    "tasks": ("hooks.before_tasks",),
    "implement": ("hooks.before_implement", "hooks.after_implement"),
    "analyze": ("hooks.before_analyze", "hooks.after_analyze"),
    "converge": ("hooks.before_converge",),
}


def _command_surface_paths(name: str) -> list[Path]:
    """Candidate installed command/skill files for a core command, one per
    known integration layout. A present path is a surface the active
    integration installed; the test accepts any of them."""
    return [
        ROOT / ".opencode" / "commands" / f"speckit.{name}.md",
        ROOT / ".github" / "skills" / f"speckit-{name}" / "SKILL.md",
        ROOT / ".claude" / "skills" / f"speckit-{name}" / "SKILL.md",
        ROOT / ".agents" / "skills" / f"speckit-{name}" / "SKILL.md",
    ]

# The project sections the extension-provided templates must contribute when
# resolved through the full stack (project-local overrides > presets >
# extension-provided > core). If resolution changes upstream and falls
# through to the core template, new specs and tasks silently lose the
# Requirements Coverage section and the tests-required stance.
EXPECTED_TEMPLATE_CONTENT = {
    "spec-template": "Requirements Coverage",
    "tasks-template": "new-code-coverage principle",
}

# The manifest's provides.templates declarations, as name -> file. The
# declaration half of the template check runs in every environment (CI
# included); the resolution half requires the installed extension.
EXPECTED_TEMPLATE_DECLARATIONS = {
    "spec-template": "templates/spec-template.md",
    "tasks-template": "templates/tasks-template.md",
}

# The workflow overlay's review gates, mirrored from the checklist
# commands. Composed only when the overlay's insert_after step ids still
# match the bundled workflow's steps.
EXPECTED_WORKFLOW_GATES = (
    "review-coverage",
    "review-plan-checklist",
    "review-tasks",
    "review-implement-checklist",
    "review-diff",
    "review-final-tree",
)


def _assert_requirements_extension_surfaces() -> None:
    """Gate the extension's mirror tests on adoption, not on file presence.

    The two-tier rule the enforcement mirror tests follow: a project that has
    not adopted the requirements extension (no extensions/requirements
    source tree) has none of these surfaces, and its mirror tests skip with
    this stated reason; a project that HAS adopted it must carry its
    integral files - the manifest declaring commands, hooks, and
    templates, the tracked hook registration
    (.specify/extensions.yml) the skills fire, and the workflow
    overlay the commands themselves claim the checklists fire as
    gates - and a missing one is a broken enforcement chain that must
    fail ``make test``, not skip past it. Gating on each file's
    presence instead of on adoption would turn a wiped registration
    into a silent skip that ``make test`` passes, and would leave a
    deleted overlay uncaught in CI, where the composition test skips
    for lack of the specify CLI."""
    if not EXTENSION_SOURCE.is_dir():
        pytest.skip("requirements extension not adopted in this project")
    missing = [
        path
        for path in (MANIFEST, EXTENSIONS_YML, GATES_YML)
        if not path.is_file()
    ]
    assert not missing, (
        f"requirements extension present but integral files missing: "
        f"{[str(path.relative_to(ROOT)) for path in missing]}; a deleted "
        f"manifest, hook registration, or workflow overlay is a broken "
        f"enforcement chain, not an absent surface. Reinstall: {REINSTALL}"
    )


def test_hook_registrations_present():
    """The extension's eight mandatory hooks are registered in
    .specify/extensions.yml with optional: false.

    The installer manages the hooks section: a reinstall purges and re-adds
    whatever the manifest declares, so a manifest that lost its hooks section
    would silently wipe the registrations and the enforcement checks would
    stop firing. The test asserts the full firing-relevant shape including
    enabled and condition: a registration with enabled: false or a
    non-empty condition is a silent no-fire that leaves every other test
    green. Also a can-it-fail guard: the assertion is on the exact
    expected set, so an empty or partial hooks section fails. Skips
    only when the extension itself is not adopted; a deleted
    registration with the extension present fails here - a wiped
    registration is the failure this module exists to catch."""
    _assert_requirements_extension_surfaces()
    config = yaml.safe_load(EXTENSIONS_YML.read_text(encoding="utf-8"))
    hooks = config.get("hooks") or {}
    observed = {
        (
            event,
            entry.get("command"),
            entry.get("optional"),
            entry.get("enabled"),
            entry.get("condition"),
        )
        for event, entries in hooks.items()
        for entry in entries
    }
    assert observed == EXPECTED_HOOKS, (
        f"hook registrations diverge from the extension manifest; expected "
        f"{sorted(EXPECTED_HOOKS)}, observed {sorted(observed)}. "
        f"Reinstall: {REINSTALL}"
    )


def test_installed_command_surface_surfaces_hooks():
    """Every installed core command surface this project's hooks ride on still
    carries its hook-check sections.

    The registrations fire only if the command instructions surface them: a
    future re-vendor of the core commands could drop or rename the
    ``hooks.<event>`` keys and the enforcement checks would silently stop
    being injected. Checks whichever integration layout is installed (opencode
    commands, or copilot/claude/agy skills); skips only when no core command
    surface is installed at all (a seeded repository before vendoring)."""
    present = {
        name: [p for p in _command_surface_paths(name) if p.is_file()]
        for name in EXPECTED_HOOK_SECTIONS
    }
    if not any(present.values()):
        pytest.skip("no core command surface installed in this project")
    missing: list[str] = []
    for name, hook_keys in EXPECTED_HOOK_SECTIONS.items():
        paths = present[name]
        if not paths:
            missing.append(f"speckit-{name}: no installed command surface found")
            continue
        text = "\n".join(p.read_text(encoding="utf-8") for p in paths)
        for hook_key in hook_keys:
            if hook_key not in text:
                missing.append(f"speckit-{name}: missing {hook_key}")
    assert not missing, (
        "installed core commands no longer surface the hook registrations: "
        + "; ".join(missing)
        + "; re-vendor the core commands from the current spec-kit scaffold"
    )


def test_extension_templates_declared():
    """The extension manifest declares both project templates, and the
    tracked template files carry the project sections.

    CI-safe test over tracked state: a manifest that loses its
    provides.templates declarations, or a template file that loses the
    Requirements Coverage section or the tests-required stance, fails
    here in any environment, including a bare checkout. Skips only
    when the extension itself is not adopted; a deleted manifest with
    the extension present fails here."""
    _assert_requirements_extension_surfaces()
    manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    declared = {
        entry["name"]: entry["file"]
        for entry in manifest.get("provides", {}).get("templates", [])
    }
    assert declared == EXPECTED_TEMPLATE_DECLARATIONS, (
        f"extension template declarations diverge: expected "
        f"{EXPECTED_TEMPLATE_DECLARATIONS}, observed {declared}"
    )
    for name, file in declared.items():
        content = (
            ROOT / "extensions" / "requirements" / file
        ).read_text(encoding="utf-8")
        assert EXPECTED_TEMPLATE_CONTENT[name] in content, (
            f"{file} lost the project section ({EXPECTED_TEMPLATE_CONTENT[name]!r})"
        )


def test_extension_templates_resolve():
    """The extension-provided templates resolve through the full stack with
    the project sections intact.

    Asserts the resolution order (overrides > presets > extension > core)
    end to end: if an upstream change breaks it, new features silently
    generate core templates without the Requirements Coverage section and
    the tests-required stance. The tracked-side declarations and content
    are asserted by test_extension_templates_declared (CI-safe); this test
    additionally exercises the resolver, so it requires the extension to
    be installed and skips in a bare checkout (fresh clone, CI) where the
    installed tree is intentionally absent."""
    if not (ROOT / ".specify" / "extensions" / "requirements").is_dir():
        pytest.skip(
            "extension not installed in this checkout (fresh clone or CI); "
            "the tracked-side declaration and content tests cover this state"
        )
    for template, marker in EXPECTED_TEMPLATE_CONTENT.items():
        result = subprocess.run(
            ["bash", str(RESOLVE_TEMPLATE), template],
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        assert result.returncode == 0, result.stderr
        assert marker in result.stdout, (
            f"{template} resolved without the project section ({marker!r} "
            f"absent); the extension-provided template is not being used "
            f"or its content lost the section. Reinstall: {REINSTALL}"
        )


def test_workflow_gates_compose():
    """The workflow overlay's review gates compose onto the bundled
    workflow.

    The gates mirror the checklist commands in workflow mode; if the
    bundled workflow's step ids change upstream, the overlay's insert_after
    edits silently stop composing. Skips when the project has not
    adopted the extension (the seed template has no .specify/ until
    bootstrap runs) or when the specify CLI is not on PATH (CI runners
    do not install it; the composition is also verified manually in the
    upgrade runbook)."""
    _assert_requirements_extension_surfaces()
    if shutil.which("specify") is None:
        pytest.skip("specify CLI not on PATH")
    result = subprocess.run(
        ["specify", "workflow", "info", "speckit"],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert result.returncode == 0, result.stderr
    missing = [gate for gate in EXPECTED_WORKFLOW_GATES if gate not in result.stdout]
    assert not missing, (
        f"workflow overlay gates not composing: missing {missing}; the "
        f"bundled workflow's step ids may have changed upstream"
    )


# The firing-surface sentence in a manifest command description: the
# events named after "fires as the" must match the command's hook
# registrations exactly, so generated metadata can never under- or
# over-claim where a command fires.
FIRING_PHRASE = re.compile(r"fires as the (.*?) hooks?\.")


def _firing_events(description: str) -> set[str]:
    """Hook events a manifest description claims to fire on."""
    match = FIRING_PHRASE.search(description)
    if not match:
        return set()
    return set(re.findall(r"(?:before|after)_[a-z]+", match.group(1)))


def test_manifest_descriptions_match_registered_hooks():
    """Every command description names exactly the hook events the manifest
    registers it for.

    A description that says "before_tasks and before_converge" while a
    before_implement hook also fires advertises an incomplete firing
    surface, and a description naming an event with no registration makes
    the metadata lie. Both directions fail here."""
    _assert_requirements_extension_surfaces()
    manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    registered: dict[str, set[str]] = {}
    for event, entries in manifest["hooks"].items():
        for entry in entries:
            registered.setdefault(entry["command"], set()).add(event)
    problems: list[str] = []
    for entry in manifest["provides"]["commands"]:
        named = _firing_events(entry["description"])
        expected = registered.get(entry["name"], set())
        if named != expected:
            problems.append(
                f"{entry['name']}: description names {sorted(named)}, "
                f"registered for {sorted(expected)}"
            )
    assert not problems, (
        "manifest command descriptions diverge from the hook registrations: "
        + "; ".join(problems)
    )


def test_firing_surface_checker_reads_the_registration_list():
    """Can-it-fail: a description that drops or invents a hook is visibly
    different from one that names the registered set."""
    assert _firing_events(
        "Stub; fires as the before_tasks and before_converge hooks."
    ) == {"before_tasks", "before_converge"}
    assert _firing_events("Stub; fires as the before_plan hook.") == {"before_plan"}
    assert _firing_events("Stub with no firing surface.") == set()


# Each checklist rule is identified by a group of phrases that must
# ALL appear in a surface (AND, case-insensitive substrings). A single
# coarse word - "boundaries", "must", "malformed" - cannot evidence a rule
# on its own: a mirror could keep the word while dropping the rule and
# pass a single-word check, so no rule is a lone coarse word. The
# groups are the compact rule identifiers every mirror of a checklist
# carries (the shared parenthetical in the summaries, the sub-rule
# prose in the gate and the source body), so a mirror that drops any
# identifier loses that rule, and a rule retired at the source loses
# its phrases everywhere at once.
PLAN_CHECKLIST_RULES = (
    ("escape hatch", "requirement authority"),
    ("threshold", "operational"),
    ("must", "has a task"),
    ("boundaries", "specified"),
    ("raise", "catch"),
    ("fail-closed", "positive-path"),
    ("wire", "fixture"),
    ("command", "invocation path"),
    ("validator", "malformed"),
)
TASKS_CHECKLIST_RULES = (
    ("enum", "checker"),
    ("sequential", "IDs"),
    ("tests-first", "known-good"),
    ("tests-first", "known-bad"),
    ("raise", "catch"),
    ("command", "invocation path"),
    ("fail-closed", "positive-path"),
    ("validator", "malformed"),
    ("one-to-N", "partial-failure"),
    ("semantic", "violation class"),
)


def _frontmatter_description(path: Path) -> str:
    """The single-line ``description:`` value of a file's frontmatter."""
    match = re.search(
        r"^description:\s*(.+)$", path.read_text(encoding="utf-8"), re.M
    )
    assert match, f"{path.name}: no frontmatter description line"
    return match.group(1)


def _checklist_body(path: Path) -> str:
    """The command file's checklist text, frontmatter excluded.

    The summaries - frontmatter included - are written from this body,
    so asserting the markers in the body is what makes the source the
    source: a rule removed from the body must fail here even while the
    frontmatter still names it.
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    if lines and lines[0].strip() == "---":
        try:
            lines = lines[lines.index("---", 1) + 1:]
        except ValueError:
            pass  # Malformed frontmatter: keep the whole file so the
            # caller's marker assertion fails on it, not on a crash.
    return "\n".join(lines)


def _requirements_skills_vendored() -> bool:
    """Whether the requirements skills are vendored under .github/skills.

    The skills are the agent-facing copies of the extension commands; a
    project that adopted the extension without the dual-CLI skills
    layout has no skill mirrors, and the tests that read them exclude
    those surfaces with this stated reason instead of failing. The five
    skills vendor as a set, so one absent excludes the set."""
    return all(
        (SKILLS_DIR / skill / "SKILL.md").is_file()
        for skill in (
            "speckit-requirements-plan-checklist",
            "speckit-requirements-tasks-checklist",
            "speckit-requirements-remediation-loop",
            "speckit-requirements-prepare",
            "speckit-requirements-verify",
        )
    )


def test_checklist_rules_survive_into_every_mirror():
    """The source checklists carry their rules, and every surface that
    paraphrases a checklist carries them all.

    The source is asserted first: a rule removed from the command body
    fails here even if the frontmatter still names it and every mirror
    still carries the marker, so the mirrors cannot drift downward
    together with a quietly edited source. Then every compact summary
    of a checklist (manifest descriptions, hook registrations,
    workflow gates, skill frontmatter) is asserted against the same markers - a
    summary that keeps stale wording when a checklist gains a rule is
    silent drift, and the registered-hook half also fails on a
    forgotten reinstall (the installer regenerates the
    registrations from the manifest, so a manifest whose new wording
    never reached .specify/extensions.yml diverges from the committed
    mirror). The test skips only when the extension itself is not
    adopted (no checklists, no mirrors); with the extension present
    the manifest, the registration, and the workflow overlay are
    integral (the helper gate asserted them). The one optional mirror
    surface - the vendored skills - drops out with a stated reason
    when the requirements skills are not vendored, the same
    convention the core-skills test uses."""
    _assert_requirements_extension_surfaces()
    for command, rules in (
        ("plan-checklist", PLAN_CHECKLIST_RULES),
        ("tasks-checklist", TASKS_CHECKLIST_RULES),
    ):
        body = _checklist_body(
            EXTENSION_SOURCE / "commands" / f"speckit.requirements.{command}.md"
        )
        lost = [
            group
            for group in rules
            if any(phrase.lower() not in body.lower() for phrase in group)
        ]
        assert not lost, (
            f"the {command} checklist lost the rules {lost} at the source; "
            f"the mirrors follow the source, so restore the rule or retire "
            f"it consciously across the whole chain"
        )
    manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    command_descriptions = {
        entry["name"]: entry["description"]
        for entry in manifest["provides"]["commands"]
    }

    def hook_descriptions(hooks):
        return {
            (event, entry["command"]): entry["description"]
            for event, entries in hooks.items()
            for entry in entries
        }

    manifest_hooks = hook_descriptions(manifest["hooks"])
    has_skills = _requirements_skills_vendored()
    # The registration and the workflow overlay are integral once the
    # extension is adopted (the helper gate asserted both), so the
    # registered and gate mirrors are always asserted.
    installed = yaml.safe_load(EXTENSIONS_YML.read_text(encoding="utf-8"))
    installed_hooks = hook_descriptions(installed.get("hooks") or {})
    gates = {
        edit["step"]["id"]: edit["step"]["message"]
        for edit in yaml.safe_load(GATES_YML.read_text(encoding="utf-8"))["edits"]
    }
    plan_summaries = {
        "manifest command description": command_descriptions[
            "speckit.requirements.plan-checklist"
        ],
        "manifest before_plan hook description": manifest_hooks[
            ("before_plan", "speckit.requirements.plan-checklist")
        ],
        "registered before_plan hook description": installed_hooks[
            ("before_plan", "speckit.requirements.plan-checklist")
        ],
        "review-plan-checklist gate message": gates["review-plan-checklist"],
    }
    tasks_summaries = {
        "manifest command description": command_descriptions[
            "speckit.requirements.tasks-checklist"
        ],
        "manifest before_tasks hook description": manifest_hooks[
            ("before_tasks", "speckit.requirements.tasks-checklist")
        ],
        "manifest before_implement hook description": manifest_hooks[
            ("before_implement", "speckit.requirements.tasks-checklist")
        ],
        "manifest before_converge hook description": manifest_hooks[
            ("before_converge", "speckit.requirements.tasks-checklist")
        ],
        "registered before_tasks hook description": installed_hooks[
            ("before_tasks", "speckit.requirements.tasks-checklist")
        ],
        "registered before_implement hook description": installed_hooks[
            ("before_implement", "speckit.requirements.tasks-checklist")
        ],
        "registered before_converge hook description": installed_hooks[
            ("before_converge", "speckit.requirements.tasks-checklist")
        ],
        "review-tasks gate message": gates["review-tasks"],
        "review-implement-checklist gate message": gates[
            "review-implement-checklist"
        ],
    }
    if has_skills:
        plan_summaries["plan-checklist skill frontmatter"] = (
            _frontmatter_description(
                SKILLS_DIR / "speckit-requirements-plan-checklist" / "SKILL.md"
            )
        )
        tasks_summaries["tasks-checklist skill frontmatter"] = (
            _frontmatter_description(
                SKILLS_DIR / "speckit-requirements-tasks-checklist" / "SKILL.md"
            )
        )
    assert len(plan_summaries) == 4 + has_skills, (
        "plan mirror inventory changed; update this test"
    )
    assert (
        len(tasks_summaries) == 9 + has_skills
    ), "tasks mirror inventory changed; update this test"
    for checklist, summaries, rules in (
        ("plan", plan_summaries, PLAN_CHECKLIST_RULES),
        ("tasks", tasks_summaries, TASKS_CHECKLIST_RULES),
    ):
        for surface, text in summaries.items():
            lost = [
                group
                for group in rules
                if any(phrase.lower() not in text.lower() for phrase in group)
            ]
            assert not lost, (
                f"the {checklist} checklist {surface} lost the rules "
                f"{lost}; every mirror must carry the full checklist"
            )


# The seedable checklist surfaces, scanned for project-domain terms.
# The extension, the workflow overlay, and (when vendored) the
# requirements skills are domain-neutral by design (the constitution
# Part 1 pattern: universal rules in the distributed files, project
# instances recorded in the project's AGENTS.md), so a project seeded
# from these surfaces receives the process without anyone's domain
# vocabulary. The overlay is integral to an adopted extension; the
# skills are the one optional mirror, the same surface the mirror
# test treats conditionally.
DOMAIN_NEUTRAL_SURFACES = (
    EXTENSION_SOURCE / "commands" / "speckit.requirements.plan-checklist.md",
    EXTENSION_SOURCE / "commands" / "speckit.requirements.tasks-checklist.md",
    EXTENSION_SOURCE / "commands" / "speckit.requirements.diff-review.md",
    EXTENSION_SOURCE / "commands" / "speckit.requirements.remediation-loop.md",
    EXTENSION_SOURCE / "commands" / "speckit.requirements.prepare.md",
    EXTENSION_SOURCE / "commands" / "speckit.requirements.verify.md",
    MANIFEST,
    GATES_YML,
)
DOMAIN_NEUTRAL_SKILL_SURFACES = (
    SKILLS_DIR / "speckit-requirements-plan-checklist" / "SKILL.md",
    SKILLS_DIR / "speckit-requirements-tasks-checklist" / "SKILL.md",
    SKILLS_DIR / "speckit-requirements-diff-review" / "SKILL.md",
    SKILLS_DIR / "speckit-requirements-remediation-loop" / "SKILL.md",
    SKILLS_DIR / "speckit-requirements-prepare" / "SKILL.md",
    SKILLS_DIR / "speckit-requirements-verify" / "SKILL.md",
)

# Terms naming a specific product, system, or domain. Universal rules
# must not bake them in: a checklist that says "every new acme-storefront
# checkout carries a test" ships advice about a system most projects do
# not have. The shipped entry is a demonstrative placeholder; the scan
# becomes a real guard when the adopting project adds its own domain's
# terms here (fill-in checklist step 9), and the instances themselves
# belong in the project's AGENTS.md, which the checklists name.
DOMAIN_TERM_DENY_LIST = (
    "acme-storefront",
)


# Attribution lines name the publishing project, not its rule prose:
# `author:` and `repository:` values are metadata a seeding project
# retargets, so a seeded project's own name in them is not a domain
# leak. The scan excludes these lines instead of depending on the
# seeding project's name.
ATTRIBUTION_LINE = re.compile(r"^\s*(author|repository):.*\n?", re.M)


def _strip_attribution(text: str) -> str:
    """Drop ``author:`` and ``repository:`` lines from *text*."""
    return ATTRIBUTION_LINE.sub("", text)


def _domain_term_hits(text: str) -> list[str]:
    """The deny-list terms present in *text*, at word boundaries.

    Attribution must be stripped before the call (or never scanned):
    a seeded project named for its domain would otherwise fail the scan
    on its own name. A trailing plural is matched so the list need not
    enumerate singular and plural forms separately.
    """
    hits = []
    lowered = _strip_attribution(text).lower()
    for term in DOMAIN_TERM_DENY_LIST:
        if re.search(rf"\b{re.escape(term.lower())}s?\b", lowered):
            hits.append(term)
    return hits


def test_seedable_checklist_surfaces_stay_domain_neutral():
    """No project-domain term appears in a seedable checklist surface.

    A checklist that bakes a specific system's vocabulary into a
    universal rule ("CLI wiring on its discovery or default path",
    "workload kinds", "dashboard queries") ships advice about systems
    most seeded projects do not have. Every surface is scanned at word
    boundaries for the deny
    list, with attribution lines (author, repository) excluded - a
    seeding project retargets those, so its own name in them is not a
    leak - and the inventories are asserted by count so an edit cannot
    silently shrink the scan or the list. The scan skips only when the
    extension itself is not adopted; with the extension present the
    manifest and the workflow overlay are integral (the helper gate
    asserted them), and the skill surfaces drop out when the vendored
    skills do not exist."""
    _assert_requirements_extension_surfaces()
    has_skills = _requirements_skills_vendored()
    surfaces = DOMAIN_NEUTRAL_SURFACES
    if has_skills:
        surfaces = surfaces + DOMAIN_NEUTRAL_SKILL_SURFACES
    assert len(surfaces) == (
        8 + 6 * has_skills
    ), "scan inventory changed"
    required_terms = {"acme-storefront"}
    assert required_terms <= set(DOMAIN_TERM_DENY_LIST), (
        f"deny list lost baseline terms: "
        f"{sorted(required_terms - set(DOMAIN_TERM_DENY_LIST))}; the "
        f"placeholder entry ships with the seed - removing it is a "
        f"conscious decision alongside the floor, never a silent edit"
    )
    assert len(DOMAIN_TERM_DENY_LIST) >= 1, (
        "the deny list must never ship empty; the placeholder entry "
        "demonstrates the shape - extend it with your project's domain "
        "terms (fill-in checklist step 9)"
    )
    violations = {}
    for surface in surfaces:
        hits = _domain_term_hits(surface.read_text(encoding="utf-8"))
        if hits:
            violations[str(surface.relative_to(ROOT))] = hits
    assert not violations, (
        f"project-domain terms in seedable surfaces: {violations}; the "
        f"universal rule belongs in the surface, the project instance "
        f"in AGENTS.md"
    )


def test_attribution_lines_never_trip_the_domain_scan():
    """Can-it-fail check for the attribution exclusion: a seeded project
    whose own name is a domain term (``author: acme-storefront``, a
    repository URL naming it) stays green, while the same term in rule
    prose fails the scan (verified against synthetic metadata and
    prose). Without the exclusion, the portability promise depended on
    the seeding project's name."""
    seeded_metadata = (
        "name: requirements\n"
        "author: acme-storefront\n"
        "repository: https://github.com/some-org/acme-storefront\n"
        "description: Tasks checklist (enum grounding in\n"
        "source and existing checkers, sequential IDs, tests-first with\n"
        "known-bad fixtures)\n"
    )
    assert _domain_term_hits(seeded_metadata) == []
    prose_leak = (
        "description: the acme-storefront checkout flow needs its own\n"
        "workload kinds and dashboard queries\n"
    )
    assert _domain_term_hits(prose_leak) == [
        "acme-storefront",
    ]


# The checklist-instances section the seedable checklists point at, and the pointer
# that must keep pointing. The pointers promise "recorded in
# AGENTS.md"; without a test, deleting or gutting the section leaves
# four seedable surfaces asserting content that no longer exists while
# every test stays green - a standing claim that outlives the change
# that created it belongs in make test. Markers are matched on
# whitespace-collapsed text so line wrapping cannot hide a removal.
# The AGENTS.md checklist-instances section the seedable checklists point at.
# The section must exist AND carry a non-empty record for each of the
# two instance kinds the checklists promise (the labels are the
# universal contract; the recorded values are the project's own).
CHECKLIST_INSTANCE_MARKERS = (
    "## Project checklist instances",
)

CHECKLIST_INSTANCE_RECORDS = (
    "Command surfaces:",
    "Coverage-critical artifact kinds:",
)

POINTER_SENTENCE = (
    "The command surfaces and coverage-critical artifact kinds "
    "specific to this project are recorded in `AGENTS.md`."
)


def test_checklist_instances_and_pointer_are_asserted():
    """The AGENTS.md section the seedable checklists point at exists,
    carries what the pointers promise, and the pointers exist.

    The whole design hangs on the pointer chain: a universal rule in a
    seedable file, the instances recorded in the project's AGENTS.md.
    Prose-sync keeps the skills' copies equal to the commands, but
    nothing else holds either end of the chain: both commands could
    lose the pointer, or the record could vanish, with every other gate
    green. This test holds both ends over tracked state. It skips only
    when the extension itself is not adopted; with the extension
    present, the AGENTS.md destination the checklists point at is
    integral - a missing destination is a broken pointer contract,
    not an absent surface."""
    _assert_requirements_extension_surfaces()
    agents_path = ROOT / "AGENTS.md"
    assert agents_path.is_file(), (
        "AGENTS.md missing while the requirements extension is present; "
        "the checklists' pointer has no destination"
    )
    agents = " ".join(agents_path.read_text(encoding="utf-8").split())
    missing_record = [
        marker for marker in CHECKLIST_INSTANCE_MARKERS if marker not in agents
    ]
    assert not missing_record, (
        f"AGENTS.md lost the checklist-instances section: {missing_record}; "
        f"the seedable checklists point at this section"
    )
    # The section must carry a non-empty record for each instance kind
    # the checklists promise: a bare heading with the records deleted
    # would leave every pointer dangling over an empty destination.
    # The labels are the contract; the recorded values are the
    # project's own, so only emptiness and unfilled placeholders fail.
    section_lines = agents_path.read_text(encoding="utf-8").splitlines()
    in_section = False
    recorded = {label: "" for label in CHECKLIST_INSTANCE_RECORDS}
    for line in section_lines:
        if line.strip() == CHECKLIST_INSTANCE_MARKERS[0]:
            in_section = True
            continue
        if in_section and line.startswith("#"):
            break
        if not in_section:
            continue
        for label in CHECKLIST_INSTANCE_RECORDS:
            if line.lstrip("- ").startswith(label):
                recorded[label] = line.split(":", 1)[1].strip()
    unfilled_marker = "@" + "FILL-IN" + "@"
    empty_records = [
        label for label, value in recorded.items()
        if not value or value.startswith(unfilled_marker)
    ]
    assert not empty_records, (
        f"AGENTS.md checklist-instances section is missing or has empty "
        f"records for {empty_records}; the checklists point at these "
        f"instances and every one must be recorded"
    )
    for command in ("plan-checklist", "tasks-checklist"):
        path = (
            EXTENSION_SOURCE / "commands" / f"speckit.requirements.{command}.md"
        )
        flat = " ".join(path.read_text(encoding="utf-8").split())
        assert POINTER_SENTENCE in flat, (
            f"{command}: lost the pointer to the project instances; the "
            f"universal rule needs its project instances in AGENTS.md"
        )


def test_extension_gate_fails_on_missing_integral_files(tmp_path, monkeypatch):
    """The adoption gate skips only for a non-adopting project and
    fails on a broken chain.

    Can-it-fail check for the guard direction itself: gating on each
    file's presence instead of on adoption would turn a deleted
    registration into a silent skip that ``make test`` passes, and
    would leave a deleted workflow overlay uncaught in CI. The gate's
    contract is asserted
    here against synthetic trees, so the semantics cannot regress
    unnoticed: a project that never adopted the extension skips, an
    adopting project missing any integral file (manifest,
    registration, overlay) fails, and an intact adopting project
    passes."""
    monkeypatch.setattr(f"{__name__}.ROOT", tmp_path)
    monkeypatch.setattr(
        f"{__name__}.EXTENSION_SOURCE", tmp_path / "extensions" / "requirements"
    )
    monkeypatch.setattr(
        f"{__name__}.MANIFEST",
        tmp_path / "extensions" / "requirements" / "extension.yml",
    )
    monkeypatch.setattr(
        f"{__name__}.EXTENSIONS_YML", tmp_path / ".specify" / "extensions.yml"
    )
    gates = tmp_path / ".specify" / "workflows" / "overlays" / "speckit"
    monkeypatch.setattr(
        f"{__name__}.GATES_YML", gates / "review-gates.yml"
    )

    # Never adopted: no extension source tree at all - skip.
    with pytest.raises(pytest.skip.Exception):
        _assert_requirements_extension_surfaces()

    # Adopted: the extension source tree exists.
    (tmp_path / "extensions" / "requirements").mkdir(parents=True)

    # Adopted but the registration and overlay are missing - fail,
    # never skip.
    (tmp_path / "extensions" / "requirements" / "extension.yml").write_text(
        "schema_version: '1.0'\n"
    )
    with pytest.raises(AssertionError, match="broken enforcement chain"):
        _assert_requirements_extension_surfaces()

    # Adopted but the manifest is missing - fail, never skip.
    (tmp_path / "extensions" / "requirements" / "extension.yml").unlink()
    with pytest.raises(AssertionError, match="broken enforcement chain"):
        _assert_requirements_extension_surfaces()

    # Adopted but the workflow overlay is missing - fail, never skip:
    # the composition test skips in CI for lack of the specify CLI, so
    # a deleted overlay must be caught here.
    (tmp_path / "extensions" / "requirements" / "extension.yml").write_text(
        "schema_version: '1.0'\n"
    )
    (tmp_path / ".specify").mkdir()
    (tmp_path / ".specify" / "extensions.yml").write_text("installed: []\n")
    with pytest.raises(AssertionError, match="broken enforcement chain"):
        _assert_requirements_extension_surfaces()

    # Adopted and intact - the gate passes.
    gates.mkdir(parents=True)
    (gates / "review-gates.yml").write_text("id: review-gates\n")
    _assert_requirements_extension_surfaces()


def _owned_state_snapshot():
    """Byte snapshots of the state the extension installer owns.

    Covers .specify/extensions.yml (the installer registers the installed
    list and the hooks there) and the installed extension tree (excluding
    the .specify-dev adapter directory, which carries per-install
    substituted paths and is excluded by the sync test for the same
    reason)."""
    extensions_yml = (ROOT / ".specify" / "extensions.yml").read_bytes()
    installed = ROOT / ".specify" / "extensions" / "requirements"
    tree = {
        str(p.relative_to(installed)): p.read_bytes()
        for p in sorted(installed.rglob("*"))
        if p.is_file() and ".specify-dev" not in p.relative_to(installed).parts
    }
    return extensions_yml, tree


def test_extension_reinstall_is_state_stable():
    """Running the extension install is idempotent for the state it owns.

    This is the generic owned-state detector: rather than asserting each
    claim about what the installer writes (registrations, config), it runs
    the mutating operation and asserts the resulting owned state is
    byte-identical. Any installer behaviour change - upstream or in the
    extension manifest - that rewrites state it owns shows up here, even
    for changes no enumerated test predicted. It also enforces the
    hand-edit invariant: a hand-edited .specify/extensions.yml diverges
    from the manifest-registered state, the reinstall restores the
    installer-written state, and the before/after delta fails loudly
    (the working tree is left in the correct, installer-written state).

    Requires the extension to already be installed: a bare checkout
    (fresh clone, CI) has no installed tree, and a first install is not a
    stability assertion. Skips there, and also when the specify CLI is
    not on PATH (CI runners do not install it)."""
    if not (ROOT / ".specify" / "extensions" / "requirements").is_dir():
        pytest.skip("extension not installed in this checkout; first install "
                    "is not a stability assertion")
    if shutil.which("specify") is None:
        pytest.skip("specify CLI not on PATH (run the upgrade runbook "
                    "on a machine that has it)")
    yml_before, tree_before = _owned_state_snapshot()
    result = subprocess.run(
        ["specify", "extension", "add", "--dev", "--force",
         "extensions/requirements"],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    yml_after, tree_after = _owned_state_snapshot()
    assert yml_after == yml_before, (
        "reinstall rewrote .specify/extensions.yml; the installer or the "
        "extension manifest changed the state it owns. If the change is "
        "intended, commit the new installer-written state; if not, the "
        "manifest lost a declaration (hooks) or the installer clobbered "
        "state it does not own."
    )
    changed = sorted(
        path
        for path in tree_before.keys() & tree_after.keys()
        if tree_before[path] != tree_after[path]
    )
    added = sorted(set(tree_after) - set(tree_before))
    removed = sorted(set(tree_before) - set(tree_after))
    assert tree_after == tree_before, (
        "reinstall rewrote the installed extension tree; "
        f"content changed: {changed[:5]}, added: {added[:5]}, "
        f"removed: {removed[:5]}"
    )
