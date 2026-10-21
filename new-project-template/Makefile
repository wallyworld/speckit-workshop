.PHONY: install test test-style test-traceability test-enforcement \
       test-workshop-actions test-extension _guard-uv _guard-venv

# The bootstrap-manifest mirror is template-only: seeded projects have no
# bootstrap.sh and carry no such test.
MIRROR_TESTS = test-style test-traceability test-enforcement test-workshop-actions
ifneq ($(wildcard bootstrap.sh),)
MIRROR_TESTS += test-bootstrap-manifest
.PHONY: test-bootstrap-manifest
endif

_guard-uv:
	@command -v uv >/dev/null 2>&1 || { echo "Error: 'uv' is required. Install it from https://docs.astral.sh/uv/#installation" >&2; exit 1; }

_guard-venv:
	@[ -f .venv/bin/activate ] || { echo "Error: run 'make install' first to create the virtual environment" >&2; exit 1; }

# Always install the mirror-test dependencies. Keying installation on
# .venv/bin/activate skips it when uv (or `uv run`) has already created a
# venv that is newer than requirements.txt but lacks pytest or pyyaml.
# Projects add their own suite to `test` (for example a test-app target
# that runs the application tests) and expose it as a workshop action or
# allowlist it in tests/test_workshop_actions.py.
install: _guard-uv
	uv venv 2>/dev/null || uv venv --clear
	uv pip install -r requirements.txt
	uv tool install --upgrade specify-cli

test: $(MIRROR_TESTS)

test-style: | _guard-venv
	.venv/bin/python -m pytest tests/test_style.py -v

test-traceability: | _guard-venv
	.venv/bin/python -m pytest tests/test_requirement_traceability.py -v

test-enforcement: | _guard-venv
	.venv/bin/python -m pytest tests/test_enforcement_chain.py -v

# The workshop-action sync mirror: the named actions in the .workshop
# definition must track the Makefile's public targets (both directions).
test-workshop-actions: | _guard-venv
	.venv/bin/python -m pytest tests/test_workshop_actions.py -v

ifneq ($(wildcard bootstrap.sh),)
# The bootstrap-manifest mirror: the copy manifest in bootstrap.sh must
# cover every shipped Python file under tests/ (both directions). This
# test is template-only and is not shipped to seeded projects.
test-bootstrap-manifest: | _guard-venv
	.venv/bin/python -m pytest tests/test_bootstrap_manifest.py -v
endif

# The extension Bash suite: run it directly when the extension is
# installed; the pytest mirrors also drive it under test-traceability.
test-extension:
	@if [ -d extensions/requirements ]; then \
		bash extensions/requirements/tests/run-bash-tests.sh; \
	else \
		echo "skip: extensions/requirements not installed (not a seeded project)"; \
	fi