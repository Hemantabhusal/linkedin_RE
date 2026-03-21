# linkedin_profile_scraper_python

Python implementation of the LinkedIn profile scraper worker. The project is
structured to keep configuration, HTTP session handling, payload parsing,
storage, and worker orchestration separate.

## Layout

```text
linkedin_profile_scraper_python/
  .venv/
  .env
  requirements.txt
  pyproject.toml
  main.py
  src/
    client/
    config/
    logging_setup/
    models/
    parser/
    scraper/
    storage/
    utils/
    worker/
```

## Quick start

1. Create and activate the virtualenv:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
./.venv/bin/pip install -r requirements.txt
```

3. Copy the example env file and fill it:

```bash
cp .env.example .env
```

4. Ensure the MySQL schema already exists and matches the expected tables.

5. Add pending LinkedIn profile URLs into the `profiles` table.

6. Run the worker:

```bash
./.venv/bin/python main.py
```

## Notes

- Code is written to remain compatible with Python 3.9 syntax/features.
- `curl_cffi` is used to keep the transport layer closer to browser-like TLS
  and HTTP behavior than plain `requests`.
- Set `VERBOSE_LOGGING=1` in `.env` to enable request/response diagnostics
  while developing.
