# Design and threat model

The retrieval path is intentionally local: files are read from a configured root, text chunks and hashes are stored in SQLite, and TF-IDF ranking runs in-process. No embedding API, hosted model, telemetry, or automatic network fetch is used. `/api/v1/ingest` accepts only paths that resolve inside `VAULT_LIBRARY_ROOT`, and supported extensions are allow-listed.

The demo service has no authentication. Bind it only to localhost or place it behind an authenticated gateway before exposing it. The SQLite file contains extracted document text; protect it like the source files. PDF parsing and document content are untrusted inputs; keep dependencies updated and run with a low-privilege account.
