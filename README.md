## Developer setup (quick)

1. Create and activate a virtualenv (Linux/macOS):

	python -m venv venv
	source venv/bin/activate

2. Install runtime dependencies and the package in editable mode:

	pip install --upgrade pip
	pip install -r requirements.txt
	pip install -e .

3. System dependency on Linux:

	- `python-magic` requires `libmagic` (Debian/Ubuntu package: `libmagic1`). Install it with:

	  sudo apt-get update && sudo apt-get install -y libmagic1

4. First-run model download:

	- The sentence-transformers model downloads on first use (a one-time network download). Expect ~90MB download the first time you run the tests or the app.

5. Run the backend smoke test:

	python tests/test_backend.py

Notes:

- Use a project-local venv to avoid conflicts with globally installed packages named `backend`.
- CI installs the package editable and caches Hugging Face model downloads to speed subsequent runs.
