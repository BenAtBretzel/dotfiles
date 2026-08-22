# Citation Formats Specification (`.meta.toml`)

This specification defines the syntax, schema, and field attributes for `.meta.toml` sidecar files used across repositories and agent workflows.

All metadata files use the [TOML](https://toml.io/) format with a single top-level `[meta]` table containing string key-value pairs (`key = "value"`).

---

## 1. Schema Models

### A. External Adapted Persona / Prompt Format
Used when third-party prompts, personas, or skills are adapted or integrated into a repository.

```toml
[meta]
adaptation = "Condensed and normalized for sdlcbot's persona format."
copyright_notice = "Copyright GitHub, Inc."
creator = "GitHub, Inc. and community contributors"
license = "MIT"
license_file = "LICENSES/mit-github-awesome-copilot.txt"
license_url = "https://github.com/github/awesome-copilot/blob/main/LICENSE"
original_file_name = "accessibility.agent.md"
retrieved_at = "2026-08-20"
source_location = "https://github.com/github/awesome-copilot/blob/main/agents/accessibility.agent.md"
source_repository = "https://github.com/github/awesome-copilot"
```

### B. Internal Original Persona Format
Used for internally authored personas, tools, or templates.

```toml
[meta]
creator = "sdlcbot"
license = "Apache-2.0"
retrieval_date = "2026-08-21T07:55:00-07:00"
source = "internal"
status = "original"
version = "1.0.0"
```

### C. Factual Claim, Fact, or Statement Citation Format
Used when asserting a specific claim, statistic, quote (`sic`), or factual summary derived from an authoritative source.

```toml
[meta]
claim = "HTTP/2 stream multiplexing reduces TCP connection overhead and head-of-line blocking."
creator = "Internet Engineering Task Force (IETF)"
fact = "RFC 7540 defines the binary framing layer for HTTP/2."
license = "IETF Trust"
license_url = "https://trustee.ietf.org/documents/trust-legal-provisions/"
retrieved_at = "2026-08-21"
sic = "A single HTTP/2 connection can contain multiple concurrently open streams."
source_location = "https://datatracker.ietf.org/doc/html/rfc7540#section-5"
source_repository = "https://github.com/ietf-wg-httpbis"
statement = "HTTP/2 introduces binary framing and stream multiplexing over a single TCP connection."
```

### D. Sidecar Media and Binary Asset Format
Used for binary assets, images, graphics, audio, and dataset files where metadata cannot be placed in code comments. Sidecars are located adjacent to the asset as `<original_file_name>.meta.toml`.

```toml
[meta]
creator = "World Wide Web Consortium (W3C)"
description = "Official SVG logo for WCAG 2.1 accessibility guidelines."
license = "W3C Document License"
license_url = "https://www.w3.org/Consortium/Legal/2015/doc-license"
original_file_name = "w3c-wcag-badge.svg"
retrieved_at = "2026-08-15"
source_location = "https://www.w3.org/WAI/assets/images/w3c-wcag-badge.svg"
source_repository = "https://github.com/w3c/wai-website"
```

---

## 2. Field Dictionary (Lexicographically Ordered)

| Field | Type | Description | Required / Optional |
| :--- | :--- | :--- | :--- |
| `adaptation` | `string` | Narrative explaining how the original work was altered, condensed, or refactored. | Required for external adaptations |
| `claim` | `string` | The specific assertion or claim being validated. | Optional (required for factual claims) |
| `copyright_notice` | `string` | Explicit copyright string matching upstream source. | Recommended for external works |
| `creator` | `string` | Original author, organization, or upstream maintainer. | Required |
| `description` | `string` | Human-readable summary of the associated asset. | Optional |
| `fact` | `string` | Concrete verifiable fact supported by the source. | Optional |
| `license` | `string` | SPDX identifier or license name (e.g., `MIT`, `Apache-2.0`). | Required |
| `license_file` | `string` | Relative path to local copy of license text in repository. | Recommended for external works |
| `license_url` | `string` | Public URL pointing to authoritative license document. | Recommended for external works |
| `original_file_name` | `string` | Upstream filename before renaming or ingestion. | Recommended for external works |
| `retrieval_date` | `string` | ISO 8601 timestamp or date when asset was retrieved. | Optional (alias for `retrieved_at`) |
| `retrieved_at` | `string` | Date string (YYYY-MM-DD) indicating when content was retrieved. | Required for external works |
| `sic` | `string` | Verbatim quoted text as it appears in the source material. | Optional (enables exact text matching) |
| `source` | `string` | Origin classification (e.g., `"internal"`). | Required for internal assets |
| `source_location` | `string` | Canonical direct URL to original source document or asset. | Required for external works |
| `source_repository` | `string` | Canonical repository root URL (e.g., GitHub repository URL). | Recommended for external works |
| `statement` | `string` | High-level summary statement substantiated by source. | Optional |
| `status` | `string` | Lifecycle state (e.g., `"original"`, `"adapted"`, `"deprecated"`). | Optional |
| `version` | `string` | Semantic version string (e.g., `"1.0.0"`). | Optional |
