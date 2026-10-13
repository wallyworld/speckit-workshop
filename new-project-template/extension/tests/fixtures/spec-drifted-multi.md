# Drifted fixture spec: multiple Completes RQs, some with content absent

## Requirements

- **FR-001**: An operator can select a built-in delivery profile or
  provide a valid custom profile.
- **FR-002**: Every locker station reports door activity counters.
- **FR-003**: Operations boards show delivery readiness and accounting,
  with separate boards for weekdays and weekends.
- **FR-004**: Report retention and storage capacity are configured.

| FR | Realizes RQ | Relationship |
| --- | --- | --- |
| FR-001 | SCEN-1 | Completes |
| FR-002 | TEL-2a | Completes |
| FR-003 | TEL-4 | Completes |
| FR-004 | QUAL-6 | Completes |

- **Requirement digests**: SCEN-1 sha256:acbf86cae4a134b9438cc8f551a9f7e2e63bd4187386b48ed829b0b4bcf5942e, TEL-2a sha256:7cdce0554ea7044f3ed042bf797d24e818596e33b677c543baa64b00df9154f7, TEL-4 sha256:13c78fb5681b6bfec61d8f5672d322638dd3c948e12e826afb1bf16e95a86ea9, QUAL-6 sha256:c63dd0f74a923490527f8b83d1e7e9267479a7bfbd94120684cb26ab50dc7caf
