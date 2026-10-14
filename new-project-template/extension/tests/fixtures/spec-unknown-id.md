# Fixture spec: a Completes claim for a well-formed requirement ID
# that REQUIREMENTS.md does not define must fail closed as UNKNOWN,
# never crash on an unbound requirement-text lookup

## Requirements

- **FR-006**: Station activity reaches the regional hub through the
  station-status feed.
- **FR-007**: Run output is stored under the artifacts root by locker
  station and run identifier. The service collects delivery metrics and
  redacted structured logs.
- **FR-008**: Cleanup only removes resources proven to belong to the run; a
  target that is already absent is an idempotent success.

| FR | Realizes RQ | Relationship |
| --- | --- | --- |
| FR-006 | PLATFORM-5 | Completes |
| FR-009 | TEL-99 | Completes |
| FR-007 | ART-1, TEL-1 | Completes |
| FR-008 | ART-6 | Completes |

- **Requirement digests**: TEL-99 sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855, PLATFORM-5 sha256:5c85c76ca1107721fbc495806c19f5fffa8ff6d520a3aad8f6e391fb108ddb70, ART-1 sha256:06ea721433e4a59b848b275f40c868d00408b3341848ee3d1a628ad3d85cbb1a, TEL-1 sha256:8e14acdc703305537295174d90264ebc842508add54402b4bb88b7d4f54d11ed, ART-6 sha256:10e040a817abde1896ce0b871a333ce78e57161509a1d569981568a74e5e1898
