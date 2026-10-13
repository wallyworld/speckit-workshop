# Fixture spec: a Completes claim with no recorded requirement
# digest must fail as UNDIGESTED

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
| FR-007 | ART-1, TEL-1 | Completes |
| FR-008 | ART-6 | Completes |