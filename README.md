# Offline Knowledge Vault

A private-by-default document library and local search platform. It indexes Markdown, text, HTML, reStructuredText, and PDF files from a configured folder, splits them into source-linked chunks, and ranks results with local TF-IDF. No hosted LLM, cloud vector store, or outbound request is required.

## Features
- Recursive file ingestion with content hashes and incremental re-indexing.
- UTF-8 text extraction and PDF extraction using `pypdf`.
- Paragraph-aware chunking with overlap and source/page metadata.
- Local ranked search, snippets, citations, and index statistics.
- FastAPI service, simple browser UI, and CLI for ingest/search.
- Path sandbox: files must live under `VAULT_LIBRARY_ROOT`.

## Start
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
New-Item -ItemType Directory -Force data\library | Out-Null
python -m vault.cli ingest data\library
uvicorn vault.api:app --reload
```
Open `http://127.0.0.1:8000`; CLI search: `python -m vault.cli search "deployment rollback"`. Set `VAULT_LIBRARY_ROOT` and `VAULT_DB_PATH` to control local storage.

## Privacy
Document contents remain in the local SQLite database. Do not expose the service to untrusted networks: the demo has no user authentication. Keep library and database backups encrypted if your documents are sensitive. See [design and threat model](docs/security.md). MIT license.
