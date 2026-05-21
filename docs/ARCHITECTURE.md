# Architecture

## Overview

The application is a Python desktop app with a small provider-based search engine:

- `app.py`: Tkinter desktop UI.
- `search.py`: parallel provider orchestration, dedupe, and ranking.
- `providers.py`: built-in legal catalog, custom JSON sources, Internet Archive, Jikan, and TVmaze providers.
- `store.py`: SQLite favorites and search history.
- `models.py`: shared result models.
- `utils.py`: title normalization, HTML stripping, and match scoring.

## Provider Strategy

Providers are isolated behind a `search(query, limit)` interface. This keeps the app extendable without tying the UI to any single source.

Current providers:

- Built-in legal catalog: known public, open, or official video entries.
- Custom JSON provider: user-maintained authorized links.
- Internet Archive: public archive video metadata and pages.
- Jikan: anime metadata and trailer links.
- TVmaze: TV metadata and official/source links.

## Precision Strategy

Precision is handled by:

- Unicode normalization and case folding.
- Exact title match boost.
- Partial containment boost.
- Sequence similarity scoring.
- Provider relevance score when available.
- Deduplication by normalized title and year.

## Legal Strategy

Every result carries a `legal_status` and `legal_note`. The app opens official/source pages instead of extracting hidden stream URLs. That makes the project suitable for open-source publication and reduces copyright risk.

