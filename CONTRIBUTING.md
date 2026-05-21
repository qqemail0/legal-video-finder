# Contributing

Thanks for helping improve Legal Video Finder.

## Rules

- Only add legal, authorized, public-domain, open-license, official, or metadata-only sources.
- Do not add piracy websites, unauthorized streaming indexes, paywall bypass logic, credential sharing, or hidden stream extraction.
- Keep providers isolated behind the `search(query, limit)` interface.
- Add or update tests for scoring, parsing, dedupe, and storage behavior.
- Run verification before opening a pull request:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\verify.ps1
```

## Provider Checklist

- Clear source name.
- Clear legal status and legal note per result.
- Timeout handling.
- No crash when the provider is unavailable.
- No secrets committed to the repository.

