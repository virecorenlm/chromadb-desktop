# CLAUDE.md

Project brief for AI assistants and developers working on **chromadb_desktop**.

## 1. Project Overview

A small desktop application that wraps [ChromaDB](https://www.trychroma.com/) (a local vector database) and a sentence-transformers embedding model to index and semantically search document text (PDF, DOCX, TXT).

The intended flow: a user loads a file, the backend extracts and chunks its text, embeds the chunks with `all-MiniLM-L6-v2`, stores them in a persistent local Chroma collection, and then supports similarity search over them. A PyQt6 GUI is planned but **not yet implemented** (see "Notes for AI Assistants").

Current state: the backend (parsing + vector store) is functional and covered by a smoke test. The GUI and app entry point are empty placeholders.

## 2. Tech Stack

- **Language:** Python (CI pins 3.12; the committed venv is also 3.12)
- **Vector DB:** `chromadb >= 0.4.0` via `chromadb.PersistentClient`
- **Embeddings:** `sentence-transformers >= 2.2.0`, model `all-MiniLM-L6-v2` (~90 MB, downloaded on first use)
- **GUI (planned):** `PyQt6 >= 6.4.0`
- **File parsing:** `PyPDF2` (PDF), `python-docx` (DOCX), `python-magic` (MIME detection; needs the `libmagic` system library on Linux)
- **Also in requirements:** `langchain >= 0.0.200` (listed but not imported anywhere in project code)
- **Packaging:** setuptools with a `src/` layout (`setup.py` + minimal `pyproject.toml` build-system section)
- **CI:** GitHub Actions (`.github/workflows/ci.yml`), Ubuntu runner

## 3. Project Structure

```
chromadb_desktop/
├── main.py                        # App entry point (EMPTY placeholder)
├── Chroma_Tools_ingest_pavilion.py# Standalone bulk-ingest script (independent of the package)
├── setup.py                       # Package metadata (name: chromadb_desktop, src layout)
├── pyproject.toml                 # Build-system section only (setuptools + wheel)
├── requirements.txt               # Runtime dependencies
├── src/
│   ├── chromadb_desktop/          # The installable package
│   │   └── backend/
│   │       ├── chroma_manager.py  # ChromaDB + embedding wrapper (core logic)
│   │       └── file_parser.py     # PDF/DOCX/TXT text extraction and chunking
│   ├── gui/                       # PyQt6 UI (ALL FILES EMPTY: main_window.py, components.py)
│   └── utils/                     # Empty placeholder package
├── tests/
│   └── test_backend.py            # Standalone smoke test script (not pytest-style)
├── data/collections/              # Default ChromaDB persistence dir (sqlite + HNSW binaries, committed)
├── docs/                          # Empty
├── build/lib/                     # setuptools build artifacts (committed, stale copies of src/)
├── venv/                          # A Linux virtualenv committed to git (see gotchas)
└── .github/
    ├── workflows/ci.yml           # CI: install deps, editable install, run smoke test
    └── copilot-instructions.md    # Earlier AI-agent notes (partly outdated paths)
```

## 4. Architecture & Design

Single-process desktop app. The backend provides two orthogonal services that the (future) GUI calls into:

1. **File parsing** (`FileParser` in `file_parser.py`): detects MIME type with `python-magic`, extracts text per format, and does simple chunking (per PDF page, ~1000-char DOCX chunks, blank-line splits for TXT).
2. **Embedding + vector store** (`ChromaManager` in `chroma_manager.py`): owns a `chromadb.PersistentClient` (default path `./data/collections`), loads `SentenceTransformer('all-MiniLM-L6-v2')` at construction, and exposes collection CRUD, `add_documents`, and `search`.

Data flow:

```
file -> FileParser.parse_file(path)
     -> {success, chunks: List[str], filename, file_type, chunk_count}
     -> ChromaManager.create_collection(name)   # sets self.current_collection
     -> ChromaManager.add_documents(chunks, metadatas, ids)  # embeds + stores
     -> ChromaManager.search(query, n_results)  # embeds query, similarity search
```

Key contracts to preserve (the smoke test and future GUI depend on them):

- `FileParser.parse_file(path) -> dict` with `success: bool`, `chunks: List[str]`, and on failure an `error` string.
- `ChromaManager.add_documents(documents, metadatas=None, ids=None) -> bool`; auto-generates IDs when none given.
- `ChromaManager` methods return `bool`/`[]` on failure and log errors instead of raising (errors are swallowed by design; callers must check return values).
- Collections are created with `metadata={"hnsw:space": "cosine"}`.

`ChromaManager` holds a single `current_collection` set by `create_collection()`; `add_documents` and `search` operate on it and fail if none is selected.

**Separate from all of the above:** `Chroma_Tools_ingest_pavilion.py` is a standalone CLI ingester that watches `~/Chroma_Feed/<collection>/` folders and indexes files into a Chroma store at `~/Chroma_Data`. It uses `pypdf` (not `PyPDF2`) and Chroma's built-in `SentenceTransformerEmbeddingFunction`, and does not import the package.

## 5. Key Files

| File | Why it matters |
|---|---|
| `src/chromadb_desktop/backend/chroma_manager.py` | Core storage/embedding logic. Result shapes from `collection.query(...)` depend on the installed chromadb version. |
| `src/chromadb_desktop/backend/file_parser.py` | All text extraction. Callers expect `List[str]` chunks and the `parse_file` dict contract. |
| `tests/test_backend.py` | The only test. End-to-end smoke: parse a temp file, create collection, add docs, search. |
| `.github/workflows/ci.yml` | Source of truth for the supported environment (Python 3.12, libmagic, editable install). |
| `setup.py` | Package name/layout. `find_packages(where='src')` picks up `chromadb_desktop`, `gui`, and `utils` from `src/`. |
| `main.py` | Intended entry point, currently empty. |

## 6. Setup & Development

```bash
# 1. Virtualenv (do NOT reuse the committed venv/; create a fresh one)
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 2. Dependencies + editable install
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .

# 3. Linux only: system dependency for python-magic
sudo apt-get install -y libmagic1
# Windows note: requirements.txt lists python-magic, which needs libmagic.
# On Windows this typically requires python-magic-bin instead (not listed in the repo).

# 4. Run the smoke test (first run downloads the ~90 MB embedding model)
python tests/test_backend.py
```

- There is no pytest configuration; `tests/test_backend.py` is run directly as a script (that is also what CI does).
- There is no runnable app yet: `python main.py` does nothing because the file is empty.
- The smoke test writes `test_document.txt` into the current working directory and persists data into `./data/collections`, so runs are stateful.

## 7. Configuration

There is **no configuration system**: no environment variables, no config files, no `.env`. Settings that exist are hardcoded:

- ChromaDB persistence path: `ChromaManager(persist_directory="./data/collections")` constructor default (relative to the CWD).
- Embedding model name: `'all-MiniLM-L6-v2'` hardcoded in `chroma_manager.py` (and in the ingest script).
- Ingest script paths: `~/Chroma_Feed` (input) and `~/Chroma_Data` (store), hardcoded in `Chroma_Tools_ingest_pavilion.py`, plus its chunking constants (size 1200, overlap 200).
- Logging: `logging.basicConfig(level=INFO)` is called inside the `ChromaManager` constructor, which globally configures logging for any process that instantiates it.

## 8. Coding Conventions & Patterns

- Class-based backend services (`ChromaManager`, `FileParser`) with type hints on most public method signatures.
- Defensive error handling: nearly every method wraps its body in `try/except Exception`, logs the error, and returns a failure value (`False`, `[]`, or a `success: False` dict). Nothing raises to callers.
- Docstrings on all public methods; `snake_case` naming throughout.
- Result-dict pattern for `parse_file` (a `success` flag plus payload keys) rather than exceptions.
- `__init__.py` files declare `__all__` for the package and backend subpackage.
- Imports of project code always go through the installed package: `from chromadb_desktop.backend.chroma_manager import ChromaManager`.

## 9. Dependencies & External APIs

All processing is local; there are no external service APIs. Network access is only needed once, when Hugging Face downloads the `all-MiniLM-L6-v2` model (CI caches `~/.cache/huggingface` and `~/.cache/torch`).

| Dependency | Used for | Notes |
|---|---|---|
| `chromadb` | Vector storage and querying | `PersistentClient`; API result shapes vary by version |
| `sentence-transformers` | Embeddings | Model loaded eagerly in `ChromaManager.__init__` (slow first construction) |
| `PyQt6` | GUI | Not yet used by any code |
| `PyPDF2` | PDF parsing in `file_parser.py` | The standalone ingest script uses `pypdf` instead, which is **not** in `requirements.txt` |
| `python-docx` | DOCX parsing | |
| `python-magic` | MIME detection | Requires libmagic system library |
| `langchain` | Nothing currently | Listed in requirements but never imported |

## 10. Notes for AI Assistants

Gotchas, in rough order of how likely they are to bite you:

- **The GUI does not exist.** `main.py`, `src/gui/main_window.py`, `src/gui/components.py`, `src/gui/__init__.py`, and `src/utils/__init__.py` are all zero-byte files. Any task phrased as "fix the GUI" is really "write the GUI".
- **A full Linux virtualenv (`venv/`) is committed to git**, and there is **no `.gitignore`**. This is why `git status` shows thousands of modified files under `venv/` on Windows. Never bulk-stage with `git add -A` or `git add .`; stage specific paths. `build/lib/` (stale setuptools output), `src/chromadb_desktop.egg-info/`, `__pycache__/` directories, and the binary Chroma store under `data/collections/` are also tracked. Adding a proper `.gitignore` would be a sensible cleanup, but do not silently delete tracked data without asking.
- **`data/collections/chroma.sqlite3` is committed and mutates whenever the smoke test runs**, so running tests dirties the working tree.
- **`.github/copilot-instructions.md` is partly outdated.** It refers to `src/backend/...` and a top-level `gui/`; the real paths are `src/chromadb_desktop/backend/...` and `src/gui/`. It also warns about a `sys.path` hack in the test that has since been removed (the test now imports the installed package, which is why `pip install -e .` is required before running it).
- **Package layout quirk:** `find_packages(where='src')` exposes three top-level packages: `chromadb_desktop`, `gui`, and `utils` (see `egg-info/top_level.txt`). `gui` and `utils` are installed as bare top-level packages, not under `chromadb_desktop`. If you implement the GUI, consider whether it should move under `chromadb_desktop/` first.
- **Two parallel ingestion implementations exist** (the `ChromaManager`/`FileParser` package and the standalone `Chroma_Tools_ingest_pavilion.py` script) with different chunking, different PDF libraries, and different storage paths. They are not meant to share data. Keep changes to one from silently breaking assumptions in the other, and note the script's `pypdf` dependency is missing from `requirements.txt`.
- **Stray file:** `src/chromadb_desktop/backend/chromadb-desktop.code-workspace` is a VS Code workspace file oddly placed inside the package; it is not code.
- **CI is the environment contract:** Ubuntu, Python 3.12, `libmagic1`, editable install, then `python tests/test_backend.py`. CI triggers only on pushes/PRs to `main`; the current working branch is `feature/chromadb-desktop-package`.
- **First-run cost:** constructing `ChromaManager` downloads the embedding model if it is not cached and is slow even when cached. Avoid constructing it repeatedly in loops or per-request.
- Test files `test_document.txt` and `test_file.txt` at the repo root are fixtures/leftovers from the smoke test, not documentation.

Ambiguities (do not guess; ask the user if it matters):

- No license file, no author metadata beyond `setup.py`, and the empty `docs/` directory give no guidance on distribution intent.
- Whether `langchain` is planned for future use or is a leftover dependency is not documented anywhere.
- The intended GUI design (what `main_window.py` and `components.py` should contain) is not specified in the repo.
