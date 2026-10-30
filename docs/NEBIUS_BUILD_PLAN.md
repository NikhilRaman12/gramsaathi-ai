# Gramsaathi One — Nebius Hackathon Build Plan

## Baseline audit

- Audited branch: `nebius-hackathon`, commit `7ff42dff1f968f1897ce8ff2651ecb00cd5cbf21` (2026-03-29).
- The branch was clean before edits. The local checkout is isolated under `work/gramsaathi-ai`; its only remote is named `github` and points to `NikhilRaman12/gramsaathi-ai`.
- The repository contains a Gradio interface (`app.py`), a FastAPI wrapper (`fastapi_app.py`), a LangChain/FAISS loader, a PDF/text corpus, and an AWS Bedrock caller.
- Existing gaps: the UI displays one unstructured textbox; retrieval uses `FakeEmbeddings`; the generator allows unsupported general answers; sources lose filenames, pages, and URLs; the checked-in `index.pkl` is a Git LFS pointer whose object cannot currently be downloaded because the GitHub LFS budget is exhausted; the Dockerfile runs FastAPI while the Space card selects the Gradio SDK; there are no tests, environment examples, or project documentation; no `LICENSE` file is present although Space metadata says `apache-2.0`.
- Preserve all original PDFs and the FAISS artifacts. Do not claim that the unavailable pickle or existing index has been validated. Rebuild a deterministic local lexical fallback from the source PDFs so the app remains useful without the LFS object or an external embedding service.
- Source corpus includes agriculture and rural-development documents from 2019–2025, an October 2024 PM-KISAN release, and two tiny placeholder text files. Page-level PDF hyperlinks will be retained as evidence links where present; unlinked pages will cite filename and page only. Scanned pages with no extractable text remain a known corpus limitation.

## Verified Nebius configuration

Checked against the official [Token Factory quickstart](https://docs.tokenfactory.nebius.com/quickstart), [API reference](https://api.tokenfactory.nebius.com/docs), and [Nebius NVIDIA Nemotron model guide](https://nebius.com/services/token-factory/models/nvidia-nemotron-models-inference) on 2026-10-30:

- OpenAI-compatible chat completions endpoint: `https://api.tokenfactory.nebius.com/v1/chat/completions`.
- Authentication: `Authorization: Bearer <NEBIUS_API_KEY>`; keep the key in the process environment / Space secret.
- Request shape: `model` plus `messages`; response text is in the first choice's message content.
- Current NVIDIA model ID used by the integration: `nvidia/Nemotron-3_5-Lightning`. Nebius's current model guide lists it as a public endpoint and uses this exact ID in its API example. The smoke test also checks the authenticated `/v1/models` catalog before making an inference request, because account access can still vary.
- `NEBIUS_API_KEY` was absent from the process environment; no local `.env` file exists. `.gitignore` excludes `.env`, `.env` is not tracked, and `.env.example` is a blank, safe-to-commit template. A real inference smoke test is therefore skipped; mocked tests are reported separately.

## Implementation stages

1. Replace the Bedrock-first generator with a small provider boundary and a Nebius Token Factory HTTP client. Add timeout, sanitized errors, bounded retry for rate limiting / connection setup, and an environment-configured model. Preserve the existing optional S3 corpus utility; do not require AWS for inference.
2. Build page-aware source chunks from the existing PDFs, preserve page hyperlink metadata, and add deterministic local lexical retrieval as a fallback when the LFS-backed FAISS docstore is unavailable. Return an explicit no-evidence result instead of asking the model to guess.
3. Define and validate structured model output. Keep evidence-backed summary and action steps separate from missing facts, follow-up questions, and uncertainty. Treat all retrieved text as untrusted prompt data and validate every cited evidence ID.
4. Add a sourced PM-KISAN preliminary screening module using the current official scheme page. Make unknown facts remain unknown, show the exclusion basis and official link, and state clearly that the result is not a government decision.
5. Retain Gradio and present a responsive question flow with language choice, evidence/source links, missing information, action plan, screening, empty/no-evidence, loading, and provider-error states. Keep the FastAPI wrapper available and align container launch behavior with the Gradio Space metadata.
6. Add focused mocked tests for provider success/failure/timeout/rate-limit handling, retrieval metadata and no-evidence behavior, output validation/citation IDs, and eligibility unknown/excluded/matching cases. Add a separate real-inference smoke command that verifies model availability using the authenticated catalog and then requires `NEBIUS_API_KEY` for a live request.
7. Update setup/demo documentation, ignore secrets and generated caches, review diff and license status, run verification, then prepare a focused commit on `nebius-hackathon`. Push only intended changes to remote `github`; never force-push and do not deploy or submit the Devpost entry.

## Risks and decisions

- The missing Git LFS object prevents validating the old FAISS docstore. The implementation must never silently treat the pointer text as a loaded index.
- Several source documents are old, non-official, scanned, or contain no page links. Display the actual source and page metadata and any available link; do not invent a URL or imply that every document is current or authoritative.
- PM-KISAN screening only flags the criteria explicitly published on the official scheme page as checked on 2026-10-29. Unknown answers stay unknown; final eligibility and status must be confirmed with the official portal / local administration.
- The repo's public license is unresolved because the GitHub branch has no `LICENSE` file. Do not add a license or assert Apache-2.0 without the owner's decision.
- Hugging Face Spaces deployment compatibility will be checked locally. No public Space will be deployed or overwritten.
