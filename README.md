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

## Diagnostic Payload Dumps

Use this command to capture the exact JSON returned by a Voyager endpoint:

```bash
./.venv/bin/python main.py dump-url "/voyager/api/..." dumps/section.json
```

Use this command to dump the main profile payload used by the worker:

```bash
./.venv/bin/python main.py dump-profile "https://www.linkedin.com/in/example/" dumps/profile.json
```

This is the preferred way to add robust parsers for LinkedIn "Show all"
sections. Capture one payload each for:

- full experience
- full education
- licenses and certifications
- skills

## Optional Rich Result Columns

The worker always saves the existing scalar columns. If these optional JSON
columns exist in `profile_results`, it will also save richer section data:

```sql
ALTER TABLE profile_results
  ADD COLUMN educations JSON NULL,
  ADD COLUMN certifications JSON NULL,
  ADD COLUMN top_skills JSON NULL;
```

## Notes

- Code is written to remain compatible with Python 3.9 syntax/features.
- `curl_cffi` is used to keep the transport layer closer to browser-like TLS
  and HTTP behavior than plain `requests`.
- Set `VERBOSE_LOGGING=1` in `.env` to enable request/response diagnostics
  while developing.
