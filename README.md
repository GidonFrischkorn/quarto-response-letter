# response-letter

A Quarto extension for writing **responses to reviewers** ("revise and
resubmit" letters) that render to **PDF, DOCX, and HTML** from a single
source file.

Reviewer comments, author replies, manuscript changes, and verbatim quotes
from the revised manuscript each get a visually distinct, auto-numbered box
in every output format — colored `tcolorbox` panels in PDF, shaded
paragraph styles in Word, CSS boxes in HTML.

## Installation

```bash
quarto add GidonFrischkorn/quarto-response-letter
```

Or start a new letter from the template:

```bash
quarto use template GidonFrischkorn/quarto-response-letter
```

## Usage

```markdown
---
title: "Response to Reviewers"
format:
  response-letter-pdf: default
  response-letter-docx: default
  response-letter-html: default
---

# Reviewer 1

::: {.comment}
The reviewer's comment, quoted verbatim.
:::

::: {.reply}
Your reply. Markdown works natively here: tables, citations, `code`,
and math like $\mathcal{N}(1, 0.5^2)$.

::: {.quoted loc="Methods, p. 12"}
A verbatim passage from the revised manuscript, shown in a grey quote
box labeled "Manuscript (Methods, p. 12):".
:::
:::

::: {.changes}
- **Methods**: what changed, where
:::
```

Note: when a `.quoted` div is nested inside a `.reply` div, use four
colons (`::::`) for the outer fence.

### Numbering and cross-references

Every level-1 heading (`# Reviewer 1`) increments the reviewer counter;
every `.comment` div is labeled **Comment R.C** and receives the anchor
`#cmt-R-C` automatically. Link to it from anywhere:

```markdown
... as discussed in our reply to [Comment 1.2](#cmt-1-2).
```

Use `{{< pagebreak >}}` between reviewers for a page break in PDF and DOCX.

### Custom labels (e.g., for non-English letters)

```yaml
language:
  response-comment-label: "Kommentar"
  response-reply-label: "Antwort"
  response-changes-label: "Änderungen"
  response-quoted-label: "Manuskript"
```

## Format notes

| Format | Styling | Notes |
|---|---|---|
| PDF | breakable `tcolorbox` panels | long boxes split cleanly across pages |
| DOCX | shaded paragraph styles from `reference.docx` | ideal for co-author comments and tracked changes |
| HTML | CSS boxes, left-hand table of contents | self-contained file (`embed-resources: true`) |

**Known limitation (DOCX):** pandoc does not propagate paragraph styles
into bullet-list items, so lists inside boxes (typical for `.changes`)
render as plain lists under the bold label — structure is preserved,
shading is not. Paragraph content is shaded as expected.

**Symbols in PDF:** prefer math mode (`$\approx$`, `$\times$`) over the
literal Unicode characters `≈`/`×`, which some LaTeX fonts silently drop.

## Customizing

- **PDF box colors/spacing**: edit `_extensions/response-letter/header.tex`
  (standard `tcolorbox` options).
- **Word styles**: edit the styles `Response Comment`, `Response Reply`,
  `Response Changes`, `Response Quote`, and `Response Label` in
  `_extensions/response-letter/reference.docx` (or rebuild it with
  `tools/make_reference_docx.py`).
- **HTML**: override the classes in `response-letter.css`.

## License

MIT. Contributions and issues welcome.
