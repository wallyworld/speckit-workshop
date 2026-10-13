# Fixture requirements for traceability verification

This fixture mirrors the shape of a real REQUIREMENTS.md so the verifier's
phrase table is fully validated even when run against the extension's own
fixtures. The requirements describe a fictional parcel locker service, so
the fixtures carry no real project's vocabulary.

## Requirements

- **ART-1**: Run output is stored beneath the gitignored `artifacts/`
  root by locker station and run identifier.

- **ART-3**: Cleanup proves the identity and ownership of every
  destructive target before deletion.

- **ART-6**: Cleanup preserves unrelated lockers and treats a verified
  already-absent target as an idempotent success.

- **PLATFORM-5**: Readiness requires a linked route from the depot's
  dispatch register to the regional hub's station-status feed, so station
  activity reaches the hub for analysis.

- **QUAL-3**: Deliveries are bounded by booking controls and static
  locker caps; cleanup requires identity proof.

- **QUAL-6**: Usage reports retain 14 days by default. Before each
  delivery peak, a pilot demonstrates that report ingestion and queue,
  retry, and drop behaviour are not saturated, and that projected peak
  storage is at most 70% of discovered usable storage unless an operator
  supplies a runtime override.

- **SCEN-1**: An operator can select a built-in delivery profile or
  provide a valid custom profile.

- **SCEN-6**: The service tracks requested, accepted, attempted,
  completed, dropped, retried, failed, and cancelled deliveries. A
  logical delivery completes once; retries are separate attempts.

- **TEL-1**: The service collects delivery metrics and redacted
  structured logs.

- **TEL-2a**: Every locker station has reporting coverage for door
  activity (`station_*` counters).

- **TEL-4**: Operations boards show delivery readiness and accounting,
  achieved throughput, and station activity; the regional view includes
  separate boards for weekdays and weekends.
