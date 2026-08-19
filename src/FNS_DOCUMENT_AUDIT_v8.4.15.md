# FNS & Documents Functional Audit v8.4.15

- FNS receipt save is atomic: receipt + linked accounting transaction commit together.
- Repeated FNS receipt saves are idempotent per user/FNS ID.
- Database uniqueness protects against concurrent duplicate receipt insertion.
- Saved receipt now stores the created transaction ID.
- Signature verification validates signature metadata and rejects malformed/future timestamps.
- Contract ownership remains enforced on generate/sign/verify/PDF endpoints.
- FNS verification failures are never represented as a successful local verification.

Runtime gate: external FNS API and PDF rendering require their production dependencies/network and must be exercised in deployment CI.
