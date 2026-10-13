.PHONY: test test-style test-traceability test-enforcement

test: test-style test-traceability test-enforcement

test-style:
	python3 -m pytest tests/test_style.py -v

test-traceability:
	python3 -m pytest tests/test_requirement_traceability.py -v

test-enforcement:
	python3 -m pytest tests/test_enforcement_chain.py -v

# The extension Bash suite: run it directly when the extension is
# installed; the pytest mirrors also drive it under test-traceability.
test-extension:
	@if [ -d extensions/requirements ]; then \
		bash extensions/requirements/tests/run-bash-tests.sh; \
	else \
		echo "skip: extensions/requirements not installed (not a seeded project)"; \
	fi
