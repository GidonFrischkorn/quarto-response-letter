# Changelog

## 0.1.0 (2026-06-12) — initial release

A Quarto format extension for point-by-point responses to reviewers,
rendering PDF, DOCX, and HTML from one source file. Design informed by
published editor and publisher guidance on response letters.

- **Response blocks**: `.comment`, `.reply`, `.changes`, and `.quoted`
  fenced divs render as visually distinct boxes in all three formats;
  comments are auto-numbered per reviewer (`Comment 1.2`) with stable
  anchors (`#cmt-1-2`) for cross-references.
- **Sections**: plain `# Reviewer N` headings drive the numbering;
  `# ... {.editor}` sections number comments `E.1, E.2, …`;
  `{.unnumbered}` headings stay outside the scheme;
  `.comment .general` gives unnumbered remarks.
- **Letter metadata** (`response-letter` YAML key): journal, manuscript
  ID/title/version, revision round, editor, salutation (derived from the
  editor name when omitted), closing, and multi-line signature render as a
  letterhead and closing block in every format. All keys optional.
- **Reply status**: `status="done|partial|declined|todo"` adds label
  badges; `todo` replies emit a render warning listing every unaddressed
  comment.
- **Summary of Changes**: collected from `summary="..."` attributes on
  comments; included via `response-letter: summary: true/false` or placed
  explicitly with a `::: {.response-summary}` div.
- **Running headline**: PDF page headers show `shorttitle` (falls back to
  `title`) and the current reviewer/editor section; DOCX uses TITLE and
  STYLEREF fields with a page-number footer.
- **Figures, tables, citations**: response exhibits are numbered separately
  from the manuscript ("Response Figure 1" / "Response Table 1"), render
  inline inside boxes (nothing floats), and citations place the reference
  list after the closing.
- **Theming and i18n**: one palette (overridable via
  `response-letter: colors:`) drives PDF and HTML; every user-visible label
  localizes through `language` keys.
- **Quality**: CI renders all formats against Quarto release and
  pre-release weekly.
