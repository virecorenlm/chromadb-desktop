## Quick orientation for AI coding agents

This repository is a small desktop app that wraps ChromaDB and a sentence-transformer model to index and search document text. The goal of these instructions is to give an AI agent the project-specific facts it needs to be productive without guessing.

Key files & layout
- `main.py` — app entry point (thin runner).
- `src/backend/chroma_manager.py` — core storage/embedding wrapper around `chromadb` + `SentenceTransformer`.
- `src/backend/file_parser.py` — file parsing utility (class `FileParser`) for PDF/DOCX/TXT.
- `gui/` — PyQt6-based UI components (`main_window.py`, `components.py`).
- `data/collections/` — default persistent storage directory used by `ChromaManager` (persist_directory).
- `tests/test_backend.py` — lightweight integration-style test / smoke script.

Big-picture architecture
- Single-process desktop app. Backend provides two orthogonal services: (1) file parsing (text extraction + chunking) and (2) embedding + vector store operations. The GUI calls into these backend modules.
- Data flow: user loads file -> `FileParser.parse_file(...)` -> produces text chunks -> `ChromaManager.create_collection(...)` and `add_documents(...)` store embeddings into persistent `data/collections` via chromadb.

Important contracts (quick)
- `FileParser.parse_file(path) -> { success: bool, chunks: List[str], filename, file_type, chunk_count }` — empty/unsupported files return success=False and `error`.
- `ChromaManager.add_documents(documents: List[str], metadatas: List[Dict]=None, ids: List[str]=None) -> bool` — expects list of strings; it computes embeddings with `SentenceTransformer('all-MiniLM-L6-v2')` and calls `current_collection.add(...)`.

Developer workflows (how to run / reproduce)
- Create a virtualenv and install dependencies:

  python -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt

- Run the simple backend smoke test (note: the test file is a standalone script):

  python tests/test_backend.py

Or use pytest to run tests if you adapt imports:

  pytest -q

Key external dependencies & system requirements
- Python packages: `chromadb`, `sentence-transformers`, `PyQt6`, `PyPDF2`, `python-docx`, `python-magic`, `langchain` (see `requirements.txt`).
- System library: `python-magic` typically requires libmagic installed on Linux (e.g. `libmagic1` / `libmagic-dev` on Debian/Ubuntu) — missing this causes file type detection errors.
- The transformer model downloads on first use and requires internet access (disk cache under your Python package/model cache directories).

Project-specific gotchas & patterns to watch for
- Parser filename: historically the file was named `filer_parser.py` (missing an "e"). It has been renamed to `file_parser.py` — imports should use `backend.file_parser`.
- Test `sys.path` manipulation: `tests/test_backend.py` appends `os.path.join(os.path.dirname(__file__), 'src')` which assumes a `tests/src` layout. Be cautious — tests may fail locally until imports/paths are adjusted.
- Chroma persistence: `ChromaManager` uses `chromadb.PersistentClient(path=persist_directory)` and stores collections under `data/collections/` by default — clearing or moving this directory will change persistence state.
- Logging: `ChromaManager` configures module-level logging via `logging.basicConfig(...)` in the class constructor. Tests or other callers may get logging configured on import.

Integration points to inspect when editing
- `src/backend/chroma_manager.py` — interactions with chromadb `collection.add/query/delete` (shape of results depends on chromadb version). If you change params, update callers accordingly.
- `src/backend/file_parser.py` — file type detection via `magic.Magic(mime=True)` and content extraction functions (`parse_pdf`, `parse_docx`, `parse_txt`). These return lists of text chunks — callers expect List[str].
- GUI code in `gui/` expects the backend public methods above; keep ABI stable (method names and return shapes) or update GUI together.

Search patterns when exploring code
- Search for: `ChromaManager`, `FileParser`, `create_collection`, `add_documents`, `parse_file`, `data/collections`.
- Also search for the two spellings: `file_parser` and `filer_parser`.

When making changes, prioritize small, testable diffs
- Add unit tests under `tests/` that import from `src/` by adjusting `PYTHONPATH` or fixing the test's `sys.path` append.
- Verify: install system dependency for `python-magic`, allow model download for `sentence-transformers`, then run `python tests/test_backend.py` to smoke-test end-to-end behavior.

If anything in these notes is unclear or you want the agent to follow a different level of strictness (e.g., fix the filename mismatch automatically), say so and I will iterate.
