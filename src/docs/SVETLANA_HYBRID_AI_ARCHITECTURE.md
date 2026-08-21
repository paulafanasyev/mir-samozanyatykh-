# Светлана — Hybrid AI Architecture

## Status: architectural baseline / implementation gap audit

### Hard boundary

OmniRoute and AnyModel are external development/review infrastructure. They MUST NOT be added to this repository, runtime configuration, Docker image, Render environment, or application code.

The production project is intended to use its own AI provider configuration. The target Svetlana architecture is **hybrid**:

- **Offline/local LLM** — primary private/offline capability.
- **Online B.ai** — online capability when available and explicitly configured by the project.
- **Domain guard** — applies the same subject restrictions to both modes.
- **Document tools** — contracts/documents are produced through the project's document-generation tooling, not by treating raw model output as a finished legal document.

## Verified current repository state

1. `src/app/api/svetlana.py` currently implements a direct OpenRouter call when `OPENROUTER_API_KEY` is present and a text fallback when it is absent. This is NOT yet the target hybrid Offline + B.ai architecture.
2. `src/app/core/config.py` currently declares `OPENROUTER_API_KEY`, `OPENROUTER_MODEL_DEFAULT`, and `OPENROUTER_MODEL_CHEAP`. No B.ai provider setting is visible in this source file.
3. `src/static/svetlana_knowledge_v3.json` contains a local structured knowledge base (17 topics, version 3.0) covering self-employment/tax/support topics. It is knowledge data, not an offline LLM runtime.
4. The repository contains the Svetlana v13 avatar runtime and local Three.js vendor assets. The `OFFLINE_RUNTIME_STATUS.md` document refers to the avatar/runtime being locally vendored; that must not be confused with an offline language model.
5. The repository contains `src/app/api/contracts.py` and PDF/document services, so document generation is already represented as a first-class application capability.

## Target runtime

```text
User
  |
  v
Svetlana Core
  |
  +--> Domain Guard ------------------------------+
  |                                               |
  +--> AI Orchestrator                            |
          |                                       |
          +--> Offline LLM -----------------------+
          |                                       |
          +--> Online B.ai -----------------------+
          |
          +--> Knowledge/Retrieval
          |
          +--> Document Tooling (contracts/docs)
          |
          v
Response Validator
  |
  +--> history/memory
  +--> TTS
  +--> avatar/lip-sync
```

## Provider selection policy

1. If the user requests a supported domain task and the offline model is healthy, prefer Offline for privacy and availability.
2. Use B.ai for online-enhanced tasks when configured and available, especially where the product requires an online capability.
3. If one provider fails, fall back to the other only when the task can safely be handled there.
4. The domain guard and safety policy apply before and after provider selection.
5. Never send secrets, bank credentials, authentication tokens, or unnecessary personal data to an external model.
6. Provider choice must be observable through a non-sensitive internal mode field (`offline` / `online`) for diagnostics.

## Svetlana knowledge scope

The assistant is intentionally specialized. Supported areas include:

- self-employed work and NPD;
- taxes and tax procedures;
- laws/regulations relevant to self-employed users;
- platform support and product usage;
- documents and contracts;
- explanations of the project's own services.

For unrelated questions, prompt injection, attempts to change system rules, or unsupported legal/tax claims, Svetlana must refuse or redirect instead of improvising.

## Critical implementation gap

The current repository proves the presence of local knowledge data and the local avatar runtime, but it does **not** prove the presence of an executable offline LLM runtime/model. A model file, inference engine, model loader, and mobile/desktop resource strategy must be located in the user's source repository before claiming Offline LLM is implemented.

Likewise, the current source still contains OpenRouter-specific Svetlana code. It must not be silently replaced with an invented B.ai endpoint. The actual B.ai API contract and key variable must be verified first.

## Quality gate

No hybrid AI change is production-ready until all of the following are verified:

- Offline LLM actually loads and answers without network access.
- B.ai actually answers through the project's configured provider.
- Offline -> Online and Online -> Offline fallback works.
- Domain guard works identically for both providers.
- Prompt injection does not disable domain restrictions.
- Document generation is performed through the document toolchain.
- User history remains isolated by authenticated user.
- No provider secret is exposed to frontend/mobile clients.
- QA has tested provider outage, timeout, malformed response, and empty response.
- Security review is AAA / 10/10.

## Development-agent boundary

Kimi Code: implementation.
Claude Opus: security and architecture review.
QA agent: adversarial regression testing.
Gemini: UI/multimodal/avatar review.
Lead architect: final acceptance and GitHub integration.

These agents operate outside the production application through external tooling. Their infrastructure must never be committed to the project.
