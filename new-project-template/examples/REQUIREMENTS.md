# Greeting Service Requirements

## Requirements

- **GREET-1**: The service MUST greet each person by name using a
  personal greeting derived from the configured template.
- **LANG-1**: The service MUST accept a language parameter with a
  documented default language, and render the greeting in the selected
  language.
- **OUT-1**: Each rendered greeting MUST be written to the greeting log
  with redacted recipient data.
