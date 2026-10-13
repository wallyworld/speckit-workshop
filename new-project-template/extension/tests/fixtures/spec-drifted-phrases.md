# Drifted fixture: QUAL-3 and SCEN-6 claimed but only generic or other
# wording present

## Requirements

- **FR-004**: Each locker reports requested, accepted, attempted,
  completed, dropped and failed deliveries; the run records accounting.
- **FR-005**: The service validates booking configuration and refuses a
  run when bounds exceed limits.
- **FR-008**: Cleanup proves the identity and ownership of every
  destructive target before deletion.

| FR | Realizes RQ | Relationship |
| --- | --- | --- |
| FR-004 | SCEN-6 | Completes |
| FR-005 | QUAL-3 | Completes |
| FR-008 | ART-3 | Completes |

- **Requirement digests**: SCEN-6 sha256:c8d6cccb63c3380ea051734960426b7d968ce0aa457e81d108991e9131715418, QUAL-3 sha256:73b675e079464dcd66609db37f4df5a8b17676622d45d7b698b5e097c6e5ee7c, ART-3 sha256:74171e507e68201baf06687582eb457f8648987f21c432d843b24859451f70e2
