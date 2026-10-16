# Fixture requirements with MUST wording

- **M-1**: The service MUST record an event with a timestamp and a source.
- **M-2**: The service MUST reject duplicates, returning an error code.
- **M-3**: The service MUST NOT lose acknowledgements under retry.
- **M-4**: The service SHALL emit a summary line.
