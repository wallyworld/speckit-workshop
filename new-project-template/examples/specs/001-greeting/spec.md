# Feature Specification: Greeting Path

**Feature Branch**: `001-greeting`

**Status**: Draft

**Input**: Parent roadmap: `ROADMAP.md` -> entry **R1**.

## User Scenarios & Testing

*By default, an assistant or agent will read the provided feature(s) below.
The user may also specify features manually.*

### User Story 1 - A person receives a personal greeting

**As a** caller of the greeting service
**I want** the service to greet a person by name
**So that** the response is personal rather than generic.

**Given** a person named `Ada` is provided
**When** the caller requests a greeting
**Then** the response contains a greeting addressed to `Ada`, rendered from
the configured greeting template.

### User Story 2 - A greeting renders in the selected language

**As a** caller who prefers a specific language
**I want** to select the greeting language with a documented default
**So that** callers who do not select still receive a valid greeting.

**Given** the service's default language is `en`
**When** a caller provides no language parameter
**Then** the greeting renders in English.

**Given** the caller selects a supported language
**When** the service renders the greeting
**Then** the greeting renders in the selected language.

### User Story 3 - A logged greeting carries no personal data

**As an** operator reading the greeting log
**I want** logged greetings to carry redacted recipient data
**So that** the log is safe to retain and share.

**Given** a greeting is rendered for a person
**When** the greeting is written to the log
**Then** the log entry contains the greeting with the recipient's name
redacted.

### Edge Cases

- An empty name renders the default greeting template without a name.
- An unsupported language falls back to the default language.

## Requirements

### Functional Requirements

- **FR-001**: The service MUST greet each person by name using a personal
  greeting derived from the configured template.
- **FR-002**: The service MUST accept a language parameter with a
  documented default language, and render the greeting in the selected
  language.
- **FR-003**: Each rendered greeting MUST be written to the greeting log
  with redacted recipient data.

## Requirements Coverage

Roadmap entry: `ROADMAP.md` -> **R1**

- **Completes**: GREET-1, LANG-1, OUT-1
- **Advances**: (none)
- **Requirement digests**: GREET-1 sha256:53d6c97bd90dba18c9448e9a91cffd929eace121e557be2d32076366e3424a02, LANG-1 sha256:625819643586729f60155134e09b794920011173c347f501d9b6d54792baefc4, OUT-1 sha256:7ce6dfabb00020bef10be1429be7e5939906abdebc7853549a296e810099fb8f

| FR | Realizes RQ | Relationship |
| --- | --- | --- |
| FR-001 | GREET-1 | Completes |
| FR-002 | LANG-1 | Completes |
| FR-003 | OUT-1 | Completes |

## Success Criteria

### Measurable Outcomes

- A greeting request for a named person returns a greeting addressed to
  that person, in the selected or default language.
- The greeting log contains redacted entries only.

## Assumptions

- The greeting template and the default language are fixed configuration;
  changing them is out of scope for this feature.
