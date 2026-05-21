# Requirements

## Product Boundary

Legal Video Finder is a desktop discovery tool for legal video resources. It can search public metadata, official pages, trailers, public archive pages, open movie catalogs, and user-provided authorized sources.

It must not scrape piracy websites, bypass paywalls, expose unauthorized stream URLs, or encourage copyright infringement.

## Core Requirements

- Search anime, films, shows, public video archives, and custom legal sources from one desktop interface.
- Rank results by title similarity and provider relevance.
- Deduplicate repeated titles across providers.
- Mark every result with provider, confidence, legal status, and legal note.
- Open official watch/source pages in the default browser.
- Save favorites locally.
- Store recent search history locally.
- Allow a user-owned `data/custom_sources.json` file for authorized sources.
- Provide open-source governance files and reproducible verification commands.

## Acceptance Criteria

- The app runs with Python standard library only.
- Searching does not require a paid API key for the included providers.
- Network provider failures do not crash the app; they are shown as partial-source errors.
- Unit tests cover scoring, dedupe, custom source loading, favorites, and history.
- Documentation clearly states the legal boundary.

