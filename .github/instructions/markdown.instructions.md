---
description: 'Documentation and content creation standards'
applyTo: '**/*.md'
---

## Markdown Content Rules

The following markdown content rules are enforced. They are tailored to the current repository style (see `README.md`).

1. **Headings**: Use hierarchical heading levels. `#` (H1) is allowed in top-level project documents like `README.md`. For secondary docs prefer starting at H2 (`##`). Avoid skipping levels.
2. **Lists**: Use `-` (preferred) or `*` for unordered lists; keep one space after the marker. Numbered lists use `1.` for every item (Markdown auto-increments). Indent nested lists by two spaces.
3. **Code Blocks**: Use fenced code blocks with a language identifier when possible (e.g. ```python). Use ```text or omit the language only when none applies.
4. **Links**: Use `[text](URL)`; make link text descriptive (avoid raw URLs unless necessary). Validate external links periodically.
5. **Images**: Use `![alt text](path_or_url)` with concise, meaningful alt text. Prefer relative paths for repo images.
6. **Tables**: Use pipes `|` with a header row and separator. Keep columns aligned for readability (not mandatory for CI).
7. **Admonitions**: Blockquote style notes like `> [!NOTE]` / `> [!WARNING]` are permitted (consistent with README). Keep them succinct.
8. **Line Length**: Soft-wrap prose roughly at 120 characters (consistent with project code style). Hard limit 400 characters per line to aid review tooling.
9. **Whitespace**: Use single blank lines to separate logical sections and before/after headings, lists, and fenced code blocks. Avoid trailing spaces.
10. (Reserved) Removed front matter rule – front matter is not used in this repository documentation.

## Formatting and Structure

Key structural guidance (refined to avoid contradictions):

- **Headings**: H1 reserved for top-level doc (README / main guide). Sub-documents start at H2. Avoid H5+; if you reach them, reconsider structure.
- **Lists**: Prefer `-` but `*` accepted. Maintain consistent marker within a single list.
- **Paragraph Wrapping**: Wrap at ~120 chars (soft). Do not forcibly break inside inline links or code.
- **Inline Code**: Use backticks for identifiers, filenames, CLI flags, and short code (`README.md`).
- **Code Blocks**: Always specify language unless plain text / logs.
- **Admonitions**: Use sparingly for user-impacting notes, warnings, or tips.
- **Images**: Provide alt text; if decorative, still supply a short description.
- **Tables**: Keep minimal; avoid overly wide tables that harm mobile readability.
- **Whitespace**: Single blank line separation; avoid double blank lines except to visually isolate large sections.

## Validation Requirements

Automated or manual checks should confirm:

- **Heading hierarchy** is consistent and starts at an appropriate level (H1 only where justified).
- **List style** consistent within each list.
- **Code fences** have language hints (except plain text / logs).
- **Links** are valid (no obvious 404) and descriptive.
- **Alt text** present for images.
- **Line length** generally within soft 120 char guideline (hard < 400).
- **No trailing whitespace** or accidental double blank lines.
  (No front matter fields required.)

<!-- Front matter section intentionally removed as blog-style posts are out of scope. -->

## Examples

Admonition:

> [!NOTE]
> This integration batches API requests to stay within rate limits.

Image:

`![Inverter Controls](inverter_controls.png)`

List (preferred dash):

```
- Control storage modes
- Schedule charge/discharge
```

Code fence with language:

```python
def example():
    return "ok"
```
