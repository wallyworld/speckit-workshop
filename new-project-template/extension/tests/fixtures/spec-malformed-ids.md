# Fixture spec: a malformed requirement ID inside a Completes cell must
# fail closed, not be silently ignored

## Requirements

- **FR-006**: Station activity reaches the regional hub through the
  station-status feed.
- **FR-007**: Run output is stored under the artifacts root by locker
  station and run identifier. The service collects delivery metrics and
  redacted structured logs.
- **FR-008**: Cleanup only removes resources proven to belong to the run.

| FR | Realizes RQ | Relationship |
| --- | --- | --- |
| FR-006 | PLATFORM-5 | Completes |
| FR-007 | ART-1, TEL-1 | Completes |
| FR-008 | ART_6 (typo) | Completes |

- **Requirement digests**: PLATFORM-5 sha256:5c85c76ca1107721fbc495806c19f5fffa8ff6d520a3aad8f6e391fb108ddb70, ART-1 sha256:06ea721433e4a59b848b275f40c868d00408b3341848ee3d1a628ad3d85cbb1a, TEL-1 sha256:8e14acdc703305537295174d90264ebc842508add54402b4bb88b7d4f54d11ed
