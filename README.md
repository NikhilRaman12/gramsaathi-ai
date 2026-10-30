---
title: Gramsaathi One
emoji: 🌾
colorFrom: green
colorTo: yellow
sdk: gradio
sdk_version: 4.44.1
app_file: app.py
pinned: false
---

# Gramsaathi One — Rural Intelligence & Action Agent

Gramsaathi One helps farmers and rural residents turn a question into a source-backed next step. It searches the repository's agriculture and rural-development documents, shows the matching source and page, asks the model for a structured explanation and action plan tied to those sources, and makes missing facts and uncertainty visible.

It is a research and navigation aid. It does not approve a scheme benefit, verify a beneficiary record, diagnose a crop, or replace a local agriculture officer.

## What this build adds

- Nebius Token Factory chat-completions inference with an NVIDIA Nemotron model ID configurable by environment variable.
- Page-aware local retrieval with source filenames, page numbers, document dates, and HTTP(S) links embedded in the PDF pages.
- A deterministic lexical retrieval path built from the existing PDF corpus. The original FAISS files stay in the repository, but the app does not use the old random `FakeEmbeddings` path or claim the unavailable LFS pickle is usable.
- Structured source-linked summaries and action steps, follow-up questions, uncertainty notes, prompt-injection handling, and a no-evidence response that avoids inference calls.
- An optional PM-KISAN preliminary screen based on the official scheme page. It keeps unknown answers unknown and never labels a user officially eligible.
- A Gradio interface with English/Hindi answer selection, evidence cards, mobile-friendly layout, and explicit empty/error states. A FastAPI wrapper remains available.

## Architecture

1. `scripts/chunk_pdfs.py` extracts PDF pages and non-empty text files into chunks and carries page-level link annotations forward.
2. `scripts/retriever.py` ranks those chunks locally with BM25 and returns source metadata. It does not make an embedding request.
3. `scripts/generator.py` sends only the user question and retrieved passages to Nebius Token Factory. The prompt treats both as untrusted input. The returned JSON is checked and citations are restricted to IDs retrieved for that request.
4. `scripts/eligibility.py` applies explicit PM-KISAN screen rules to user-selected yes/no/unknown answers without calling the model.
5. `app.py` renders the Gradio experience; `fastapi_app.py` exposes `/ask` and `/health` for API use.

The document set is mixed: it includes official scheme material, reports and research, dates from 2019 through 2025, and some scanned pages without extractable text. The app shows dates and available source links so users can judge relevance. The current BM25 search is lexical; it can miss paraphrases and Hindi queries against English-only pages.

## Nebius Token Factory configuration

The provider uses the official OpenAI-compatible endpoint documented by Nebius:

- Base URL: `https://api.tokenfactory.nebius.com/v1`
- Chat-completions route: `/chat/completions`
- Authentication: Bearer token from `NEBIUS_API_KEY`
- Default model ID: `nvidia/Nemotron-3_5-Lightning` (the current public Nemotron endpoint shown in Nebius's model guide)

Model access is tied to the Token Factory API key and may change. Confirm that the selected model appears in the key's model catalog. Override the default with `NEBIUS_MODEL` if needed.

| Variable | Default | Purpose |
| --- | --- | --- |
| `NEBIUS_API_KEY` | unset | Token Factory secret; required for inference |
| `NEBIUS_MODEL` | `nvidia/Nemotron-3_5-Lightning` | Key-accessible model ID |
| `NEBIUS_BASE_URL` | `https://api.tokenfactory.nebius.com/v1` | OpenAI-compatible API base URL |
| `NEBIUS_TIMEOUT_SECONDS` | `45` | Per-request timeout |
| `PORT` | `7860` | Gradio listen port |

Set the key through the host environment, a local ignored `.env` file, or the Hugging Face Space secret settings. Environment variables take precedence over `.env`. Never commit or screenshot a real key, and never paste it into chat.

### Local run

Python 3.10 is used by the Space configuration and `runtime.txt`.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
notepad .env
# Add your key locally to NEBIUS_API_KEY in .env, save, then close Notepad.
python app.py
```

The repository `.gitignore` excludes `.env`; verify with `git check-ignore -v .env`. `.env.example` is a tracked blank template and contains no key. You can set `$env:NEBIUS_API_KEY` instead; an already-set environment value takes precedence over `.env`.

The app listens on port 7860 by default and does not create a public Gradio share link. To run the optional API instead, use a second terminal:

```powershell
uvicorn fastapi_app:app --host 127.0.0.1 --port 7861
```

Then call `POST http://127.0.0.1:7861/ask` with `{"query":"...","language":"en"}` or use `language: "hi"` for Hindi output. `/health` is a basic process check.

## Verification

Run the offline mocked tests:

```powershell
python -m unittest discover -s tests -v
```

The smoke command checks the key's live `/v1/models` catalog for the selected model first, then makes one real chat-completions request. Run it only after configuring `NEBIUS_API_KEY` in the environment or ignored `.env`:

```powershell
python -m scripts.smoke_nebius
```

The smoke script prints success only after the live endpoint returns content. Mocked provider tests do not prove live credentials, model access, or inference. Do not report a live call as verified unless this command succeeds with a real key.

## Optional PM-KISAN screen

The screen checks the answers against requirements and listed exclusions on the [official PM-KISAN portal](https://pmkisan.gov.in/). The rules were checked on 2026-10-29. The State/UT administration identifies beneficiaries, and the portal has additional checks for beneficiary status; this screen is not a final eligibility or payment determination. If rules change, update the facts and checked date in `scripts/eligibility.py` after re-reading the official page.

## Three-minute demo outline

1. Ask a realistic question such as: “My PM-KISAN payment is delayed. What should I check?” Show the source cards, page references, links, and the missing details the app asks for.
2. Open the optional PM-KISAN screen. Leave facts unknown to show follow-up fields, then select a listed exclusion to show a preliminary flag. Show the official-source link and disclaimer.
3. Ask an unrelated question such as “How do I detect quantum entanglement on Mars?” to show that no evidence is returned and the model is not called.
4. In a terminal, run `python -m scripts.smoke_nebius` with a configured key and show the successful response from the configured NVIDIA model. If the real call has not succeeded, say so and do not describe it as live inference.

## Deployment and limitations

- The Hugging Face Space metadata selects the Gradio SDK; `app.py` is the Space entry point. The Dockerfile also starts the same Gradio app on port 7860. `fastapi_app.py` is optional and is not the container's default command.
- No Space deployment or overwrite is performed by this repository change.
- GitHub's current LFS quota prevented downloading `data/faiss_index/index.pkl`. The old FAISS artifact is preserved, but its contents and retrieval quality could not be checked. Runtime retrieval therefore uses the source files.
- Scanned pages may have no extracted text, and the local lexical retriever is not multilingual semantic search.
- Many documents are dated or not primary government rules. Verify consequential information using the cited official link and current local guidance.
- The branch has no checked-in `LICENSE` file. The previous Space card said `apache-2.0`, but that label alone does not establish the repository's public license; the license remains to be confirmed by the project owner.
- On 2026-10-30, neither the process environment nor the local project `.env` contained `NEBIUS_API_KEY`; a real inference call remains unverified until the smoke script succeeds with a valid key.

## Evidence and provider references

- [Nebius Token Factory quickstart](https://docs.tokenfactory.nebius.com/quickstart)
- [Nebius Token Factory API reference](https://api.tokenfactory.nebius.com/docs)
- [Nebius and NVIDIA Nemotron integration](https://nebius.com/services/token-factory/nemotron)
- [PM-KISAN official portal](https://pmkisan.gov.in/)
- Existing local document corpus: `data/` (see `data/source_manifest.json` for document names and dates)
