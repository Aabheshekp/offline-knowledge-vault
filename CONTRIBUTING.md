# Contributing

1. Preserve the library-root path boundary and supported-extension allow-list.
2. Document chunking, ranking, and index format changes.
3. Keep document content out of Git and do not add network-backed retrieval by default.
4. Treat documents as untrusted input and keep local storage behavior explicit.
5. Use a focused branch and describe any privacy or resource impact.

The CI workflow currently checks dependency installation and Python compilation.
