---
name: meta-toml-citation-verifier
description: >-
  Discovers, parses, partitions, and verifies .meta.toml citation sidecars and claims
  against authoritative web sources using parallel subagents. Emits Markdown reports
  and supports GitHub pull request reviews via gh CLI.
---

# Meta TOML Citation Verifier

The **Meta TOML Citation Verifier** skill audits `.meta.toml` citation sidecars, extracts claimed statements and attribution metadata, partitions citations into 4 balanced groups, and spawns parallel subagents to substantiate that external sources exist and factually back asserted claims, quotes (`sic`), adaptations, and licensing.

---

## 1. Workflow Overview

```text
Discovery & Diff (Local or PR)
           │
           ▼
TOML Extraction (yq)
           │
           ▼
4-Way Partitioning (jq)
           │
     ┌─────┴─────┬───────────┬───────────┐
     ▼           ▼           ▼           ▼
[Subagent 1] [Subagent 2] [Subagent 3] [Subagent 4]
(Group 1)   (Group 2)   (Group 3)   (Group 4)
  Web /       Web /       Web /       Web /
  Fetch       Fetch       Fetch       Fetch
     │           │           │           │
     └─────┬─────┴───────────┴───────────┘
           ▼
Aggregation & Substantiation Summary
           │
     ┌─────┴─────────────────────────────┐
     ▼                                   ▼
Markdown Report Artifact        GitHub PR Review & Comment
(Summary & Detailed Table)      (gh CLI with Mandatory Disclaimer)
```

---

## 2. Step-by-Step Verification Procedure

### Step 1: Discover and Extract Citations
Identify all target `.meta.toml` files within the target scope:

- **Full Workspace / Directory Mode**:
  Scan target folder (e.g., `sdlcbot/personas/ext/`):
  ```bash
  find <TARGET_DIR> -type f -name "*.meta.toml" | sort
  ```

- **GitHub Pull Request Mode**:
  Query changed files using `gh`:
  ```bash
  gh pr diff <PR_NUMBER> --name-only | grep '\.meta\.toml$' || true
  ```
  If local file inspection is needed for a PR not checked out in the current branch, clone or checkout into a session-scoped temporary directory under the conversation scratchpad (e.g., `<appDataDir>/brain/<conversation-id>/scratch/pr-<PR_NUMBER>/`).

### Step 2: Parse and Partition into 4 Groups
Use `yq` to parse TOML sidecars into JSON and partition the citations into exactly 4 balanced groups using the helper script or pipeline:

```bash
# Execute partition script
./scripts/partition_citations.sh --dir <TARGET_DIR> --groups 4 --output json
```

Or via direct pipeline:
```bash
find <TARGET_DIR> -name "*.meta.toml" -type f | sort | while IFS= read -r f; do
  yq -p=toml -o=json '.meta + {"file": filename}' "$f"
done | jq -s '
  def partition4:
    . as $all |
    [range(4)] | map(. as $idx | {
      group_id: ($idx + 1),
      citations: [ $all[range($idx; ($all | length); 4)] ]
    } | .count = (.citations | length));
  partition4
'
```

### Step 3: Spawn Parallel Subagents for Web Verification
For each non-empty partition group (Groups 1 through 4), spawn a `research` subagent using `invoke_subagent`:

```json
{
  "Subagents": [
    {
      "TypeName": "research",
      "Role": "Citation Verifier Group 1",
      "Prompt": "Verify Group 1 citations. For each citation in the payload:\n1. Check reachability of source_location / source_repository using read_url_content or search_web.\n2. Verify that source content factually backs any claim, fact, summary, statement, adaptation, or sic quote.\n3. Verify creator and license match upstream source.\n4. Return structured JSON with status (VERIFIED, PARTIAL, UNSUPPORTED, UNREACHABLE, INTERNAL_EXEMPT), verified aspects, and evidence quote."
    },
    {
      "TypeName": "research",
      "Role": "Citation Verifier Group 2",
      "Prompt": "Verify Group 2 citations using web tools. Follow the verification rubric in references/verification-rubric.md."
    },
    {
      "TypeName": "research",
      "Role": "Citation Verifier Group 3",
      "Prompt": "Verify Group 3 citations using web tools. Follow the verification rubric in references/verification-rubric.md."
    },
    {
      "TypeName": "research",
      "Role": "Citation Verifier Group 4",
      "Prompt": "Verify Group 4 citations using web tools. Follow the verification rubric in references/verification-rubric.md."
    }
  ]
}
```

### Step 4: Web Verification Rules for Subagents
Subagents follow the verification criteria documented in [references/verification-rubric.md](references/verification-rubric.md):

1. **Reachability Check**:
   - Query `source_location`, `source_repository`, or `license_url` using `read_url_content` or `search_web`.
   - Mark `UNREACHABLE` if URL returns 404, 410, DNS error, or invalid domain.
2. **Substantiation Check**:
   - **Verbatim quotes (`sic`)**: Search fetched document text for exact matching string.
   - **Claims / Facts / Summaries**: Confirm the source directly supports the factual proposition.
   - **Persona Adaptations**: Confirm upstream prompt repository and file exist and reflect the adaptation basis.
   - **Internal Exemptions**: If `source = "internal"`, verify internal schema completeness and mark `INTERNAL_EXEMPT`.
3. **Attribution & Licensing**:
   - Verify `creator` and `license` match upstream repository headers or license files.
4. **Status Assignment**:
   - Assign one of: `VERIFIED`, `PARTIAL`, `UNSUPPORTED`, `UNREACHABLE`, `INCOMPLETE`, `INTERNAL_EXEMPT`.

### Step 5: Aggregate Results & Generate Output
Collect outputs from all 4 subagents and produce two mandatory sections:

#### Section 1: Summary of Citation Substantiation Attempts
A high-level statistical summary:
- Total Citations Discovered
- External Citations Processed
- Internal / Exempt Citations
- Fully Verified (`VERIFIED`)
- Partially Verified (`PARTIAL`)
- Unsupported / Contradicted (`UNSUPPORTED`)
- Unreachable / Dead Links (`UNREACHABLE`)
- Incomplete Metadata (`INCOMPLETE`)
- Overall Substantiation Pass Rate (%)

#### Section 2: Detailed Enumeration Table
An itemized table listing every citation evaluated:
- `#`: Item number.
- `Citation File / Subject`: Path to `.meta.toml` file and asset name.
- `Claim / Adaptation / Attribution`: Asserted claim, fact, summary, verbatim quotation (`sic`), or adaptation description.
- `Source URL`: Clickable markdown link to the authoritative web source.
- `What Was Verified`: Specific checks performed (existence, text match, license, creator).
- `Result`: Verification status code (`VERIFIED`, `PARTIAL`, `UNSUPPORTED`, `UNREACHABLE`, `INTERNAL_EXEMPT`).
- `Evidence / Notes`: Specific quote or finding confirming or refuting the citation.

---

## 3. Output Modes

### Mode A: Markdown Report Emission
When generating a local report or artifact:
1. Format output in GitHub-flavored markdown (`-t gfm`).
2. Write report to `<appDataDir>/brain/<conversation-id>/citation-verification-report.md`.
3. Include collapsible `<details><summary>` blocks for full raw subagent verification evidence.

### Mode B: GitHub Pull Request Review
When reviewing a GitHub Pull Request:
1. Fetch PR details using `gh pr view <PR_NUMBER>` and list changed files with `gh pr diff <PR_NUMBER> --name-only`.
2. If temporary cloning is required, create an isolated directory under `<appDataDir>/brain/<conversation-id>/scratch/pr-<PR_NUMBER>/`.
3. Run the 4-group partitioned verification on all added or modified `.meta.toml` files.
4. When posting a review or comment on the PR via `gh pr comment` or `gh pr review`:
   - **MANDATORY DISCLAIMER**: The comment **MUST** begin with the following disclaimer banner:
   ```markdown
   > [!IMPORTANT]
   > **Disclaimer**: This review reflects automated citation verification analysis performed by the Meta Citation Verifier skill. This is the skill's opinion and may not reflect those of the skill's authors or repository maintainers.
   ```
   - Follow with the substantiation summary table, itemized findings table, and recommendations.

---

## 4. Supporting Resources and References

- [README.md](README.md): Citation format documentation with extensive examples from `sdlcbot/personas/`.
- [scripts/partition_citations.sh](scripts/partition_citations.sh): CLI script using `yq` and `jq` to parse and partition citations.
- [references/citation-formats.md](references/citation-formats.md): Formal field dictionary and TOML schema specifications.
- [references/verification-rubric.md](references/verification-rubric.md): Subagent decision tree and verification rules.
- [examples/sample-verification-report.md](examples/sample-verification-report.md): Sample verification report output.
- [examples/pr-review-example.md](examples/pr-review-example.md): Sample GitHub PR review comment.
