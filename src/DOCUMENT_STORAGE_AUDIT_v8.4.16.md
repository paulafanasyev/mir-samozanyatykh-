# Document/File Storage Audit v8.4.16

## Fixed
- Private document paths now use UUID-backed filenames and are stored under `data/private`.
- Contract PDF download validates that the resolved path stays inside private storage and is owned by the authenticated contract.
- Contract signing validates the stored PDF path before overwriting it.
- Invoice PDFs now use owner-scoped private paths and path traversal protection on download.
- Uploads enforce a bounded read in addition to request-level content-length limits.
- CSV imports validate extension and enforce the 10 MiB limit before parsing.
- White-label logos are no longer returned as a fake public path: files are stored privately, filenames are sanitized, image signatures are checked, and access is owner-scoped.
- SVG uploads are limited and minimally validated before storage.
- Import deal amounts use `Decimal` rather than `float`.

## Remaining production gate
Object storage (S3/MinIO) should replace local private storage for multi-instance production deployments. The current local storage is safe from direct traversal/public exposure but is node-local.
