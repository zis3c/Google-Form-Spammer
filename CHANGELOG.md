# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- Closed-form detection uses the `/closedform` redirect, so it works in any language.

### Fixed

- A closed form now reports "Form is no longer accepting responses" instead of a parse error.

## [1.1.3] - 2026-11-22

### Added

- Checkbox Grid support: rows that allow multiple selections now send multiple values.
- CI workflow that runs the offline tests on push and pull request.
- Offline test for retry and backoff when Google returns 429.
- Regex response validation is read from the form and generated text answers are checked against it.

### Changed

- Verification treats a 200 page without the form's question text as recorded, and detects question text as short as 4 characters.
- Text answers follow common validation rules: employee IDs use `EMP-1234`, ages stay within 18-65, and bio or description answers are capped at 200 characters.
- Checkbox answers select at least two options when the question has two or more.

## [1.1.2] - 2026-11-22

### Added

- Language-agnostic response classification: a re-rendered form is detected by its own question text, so confirmation pages are not misread when the form is not in English.
- Date questions with time now send hour and minute; duration Time questions now send seconds.

### Fixed

- Date+time and duration answers are sent with all component fields Google expects.

## [1.1.1] - 2026-11-22

### Fixed

- Recognize Google's "Thank you for your response." confirmation page so successful submissions are not misclassified as rejected.

## [1.1.0] - 2026-11-22

### Added

- Submission verification: every `formResponse` HTTP 200 is classified as recorded, rejected, closed, or unverified. Rejected and closed submissions now count as failures, and unverified ones are reported separately.
- `--report <path>` writes an append-only JSONL log with one line per attempt and a run summary.
- URL allow-list that accepts only Google Forms hosts.
- Multi-page form support via `pageHistory`.
- Offline `test_core.py` covering response classification, verification stats, and the JSONL report.

### Changed

- Retry backoff is capped at 8 seconds.
- Non-transient HTTP errors (400, 401, 403, 404, and similar) are no longer retried.
- Form fetch and parse errors are reported instead of being swallowed.

### Fixed

- Date, Time, and checkbox answers are sent in the format Google Forms expects.

### Credits

- Thanks to [@BadryansahBangsawan](https://github.com/BadryansahBangsawan) for the submission verification, the `--report` JSONL log, the Google Forms URL allow-list, multi-page `pageHistory`, the Date/Time/checkbox fixes, the retry cleanup, and the offline `test_core.py` test. Submitted in #1 and merged in curated form in #2.

## [1.0.0] - 2026-01-02

Earlier release with the web configurator and form parsing. See the [v1.0.0 release](https://github.com/zis3c/Google-Form-Spammer/releases/tag/v1.0.0).

[Unreleased]: https://github.com/zis3c/Google-Form-Spammer/compare/v1.1.3...HEAD
[1.1.3]: https://github.com/zis3c/Google-Form-Spammer/releases/tag/v1.1.3
[1.1.2]: https://github.com/zis3c/Google-Form-Spammer/releases/tag/v1.1.2
[1.1.1]: https://github.com/zis3c/Google-Form-Spammer/releases/tag/v1.1.1
[1.1.0]: https://github.com/zis3c/Google-Form-Spammer/releases/tag/v1.1.0
[1.0.0]: https://github.com/zis3c/Google-Form-Spammer/releases/tag/v1.0.0
