#!/usr/bin/env python3
"""Build _extensions/response-letter/reference.docx.

Takes pandoc's default reference.docx (pass its path as argv[1]) and injects:

* the five paragraph styles used by response-letter.lua (box colors are read
  from the `response-letter: colors:` defaults in _extension.yml — the single
  source of truth for the palette),
* a running header (document title via TITLE field, current `# Reviewer N`
  heading via STYLEREF field) with a blank first page (titlePg),
* a centered page-number footer.

Re-run after pandoc upgrades if the default reference doc changes:

    quarto pandoc --print-default-data-file reference.docx > /tmp/ref.docx
    python3 tools/make_reference_docx.py /tmp/ref.docx
"""
import re
import shutil
import sys
import zipfile
from pathlib import Path

SRC = Path(sys.argv[1])
EXT_DIR = Path(__file__).resolve().parent.parent / "_extensions/response-letter"
DST = EXT_DIR / "reference.docx"

# ---------------------------------------------------------------- palette

# Background tints: fraction of the base color mixed into white. Must match
# the `tints` table in response-letter.lua so DOCX output matches PDF/HTML.
TINTS = {"comment": 0.05, "reply": 0.04, "changes": 0.12, "quoted": 0.07}


def read_palette():
    text = (EXT_DIR / "_extension.yml").read_text()
    palette = {}
    for kind in TINTS:
        m = re.search(rf'{kind}:\s*["\']?#?([0-9A-Fa-f]{{6}})', text)
        if not m:
            sys.exit(f"could not find color for '{kind}' in _extension.yml")
        palette[kind] = m.group(1).upper()
    return palette


def tint(hex6, frac):
    out = ""
    for i in (0, 2, 4):
        c = int(hex6[i:i + 2], 16)
        out += f"{round(c * frac + 255 * (1 - frac)):02X}"
    return out


# ----------------------------------------------------------------- styles

BOX = """
<w:style w:type="paragraph" w:customStyle="1" w:styleId="{sid}">
  <w:name w:val="{name}"/>
  <w:basedOn w:val="BodyText"/>
  <w:qFormat/>
  <w:pPr>
    <w:pBdr><w:left w:val="single" w:sz="{bsz}" w:space="4" w:color="{border}"/></w:pBdr>
    <w:shd w:val="clear" w:color="auto" w:fill="{fill}"/>
    <w:spacing w:before="40" w:after="120"/>
    <w:ind w:left="170" w:right="113"/>
  </w:pPr>
  {rpr}
</w:style>
"""

LABEL = """
<w:style w:type="paragraph" w:customStyle="1" w:styleId="ResponseLabel">
  <w:name w:val="Response Label"/>
  <w:basedOn w:val="BodyText"/>
  <w:qFormat/>
  <w:pPr>
    <w:keepNext/>
    <w:spacing w:before="200" w:after="20"/>
  </w:pPr>
  <w:rPr><w:b/></w:rPr>
</w:style>
"""

# List-item variant of each box style: pandoc cannot carry paragraph styles
# into real Word list items, so response-letter.lua converts lists inside
# boxes into one paragraph per item with a literal bullet, styled with these.
# basedOn inherits the border/shading; the hanging indent aligns wrapped
# lines behind the bullet.
LIST = """
<w:style w:type="paragraph" w:customStyle="1" w:styleId="{sid}List">
  <w:name w:val="{name} List"/>
  <w:basedOn w:val="{sid}"/>
  <w:qFormat/>
  <w:pPr>
    <w:spacing w:before="20" w:after="40"/>
    <w:ind w:left="425" w:right="113" w:hanging="255"/>
  </w:pPr>
</w:style>
"""


def build_styles(palette):
    spec = [
        ("ResponseComment", "Response Comment", "comment", "18",
         "<w:rPr><w:i/></w:rPr>"),
        ("ResponseReply", "Response Reply", "reply", "18", ""),
        ("ResponseChanges", "Response Changes", "changes", "18", ""),
        ("ResponseQuote", "Response Quote", "quoted", "24", ""),
    ]
    return LABEL + "".join(
        BOX.format(sid=sid, name=name, border=palette[kind],
                   fill=tint(palette[kind], TINTS[kind]), bsz=bsz, rpr=rpr)
        + LIST.format(sid=sid, name=name)
        for sid, name, kind, bsz, rpr in spec
    )


# ------------------------------------------------- running header / footer

XMLNS = ('xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
         'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"')

# Default header: document title (TITLE field, italic) left, current
# "# Reviewer N" heading (STYLEREF field) at the right tab stop.
HEADER_XML = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:hdr {XMLNS}>
  <w:p>
    <w:pPr><w:pStyle w:val="Header"/></w:pPr>
    <w:fldSimple w:instr=" TITLE \\* MERGEFORMAT ">
      <w:r><w:rPr><w:i/></w:rPr><w:t>Response to Reviewers</w:t></w:r>
    </w:fldSimple>
    <w:r><w:tab/><w:tab/></w:r>
    <w:fldSimple w:instr=" STYLEREF &quot;Heading 1&quot; \\* MERGEFORMAT ">
      <w:r><w:t>Reviewer 1</w:t></w:r>
    </w:fldSimple>
  </w:p>
</w:hdr>
"""

# First page (title page) gets an empty header.
HEADER_FIRST_XML = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:hdr {XMLNS}>
  <w:p><w:pPr><w:pStyle w:val="Header"/></w:pPr></w:p>
</w:hdr>
"""

FOOTER_XML = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:ftr {XMLNS}>
  <w:p>
    <w:pPr><w:pStyle w:val="Footer"/><w:jc w:val="center"/></w:pPr>
    <w:fldSimple w:instr=" PAGE \\* MERGEFORMAT ">
      <w:r><w:t>1</w:t></w:r>
    </w:fldSimple>
  </w:p>
</w:ftr>
"""

HDRFTR_PARTS = {
    "word/header1.xml": HEADER_XML,
    "word/header2.xml": HEADER_FIRST_XML,
    "word/footer1.xml": FOOTER_XML,
}

CONTENT_TYPE = {
    "word/header1.xml": "application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml",
    "word/header2.xml": "application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml",
    "word/footer1.xml": "application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml",
}

REL_TYPE = {
    "word/header1.xml": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/header",
    "word/header2.xml": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/header",
    "word/footer1.xml": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer",
}

REL_ID = {
    "word/header1.xml": "rIdRLhdr",
    "word/header2.xml": "rIdRLhdrFirst",
    "word/footer1.xml": "rIdRLftr",
}

SECTPR_REFS = ('<w:headerReference w:type="default" r:id="rIdRLhdr"/>'
               '<w:headerReference w:type="first" r:id="rIdRLhdrFirst"/>'
               '<w:footerReference w:type="default" r:id="rIdRLftr"/>')


def patch_content_types(xml):
    overrides = "".join(
        f'<Override PartName="/{part}" ContentType="{ctype}"/>'
        for part, ctype in CONTENT_TYPE.items()
        if f'PartName="/{part}"' not in xml
    )
    return xml.replace("</Types>", overrides + "</Types>")


def patch_document_rels(xml):
    rels = "".join(
        f'<Relationship Id="{REL_ID[part]}" Type="{REL_TYPE[part]}" '
        f'Target="{part.split("/", 1)[1]}"/>'
        for part in HDRFTR_PARTS
        if REL_ID[part] not in xml
    )
    return xml.replace("</Relationships>", rels + "</Relationships>")


def patch_document(xml):
    # header/footer references must be the first children of sectPr
    xml = re.sub(r"(<w:sectPr[^>/]*>)", r"\1" + SECTPR_REFS, xml, count=1)
    # titlePg (separate first-page header) sits late in the sectPr schema
    # order: before docGrid if present, otherwise just before the close.
    if "<w:titlePg" not in xml:
        if "<w:docGrid" in xml:
            xml = xml.replace("<w:docGrid", "<w:titlePg/><w:docGrid", 1)
        else:
            xml = xml.replace("</w:sectPr>", "<w:titlePg/></w:sectPr>", 1)
    return xml


# ------------------------------------------------------------------- main

def main():
    palette = read_palette()
    styles = build_styles(palette)
    shutil.copy(SRC, DST)

    tmp = DST.with_suffix(".tmp")
    with zipfile.ZipFile(DST) as zin, \
         zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/styles.xml":
                text = data.decode("utf-8")
                text = re.sub(
                    r'<w:style [^>]*w:styleId="Response[A-Za-z]+".*?</w:style>',
                    "", text, flags=re.S)
                data = text.replace("</w:styles>", styles + "</w:styles>") \
                           .encode("utf-8")
            elif item.filename == "[Content_Types].xml":
                data = patch_content_types(data.decode("utf-8")).encode("utf-8")
            elif item.filename == "word/_rels/document.xml.rels":
                data = patch_document_rels(data.decode("utf-8")).encode("utf-8")
            elif item.filename == "word/document.xml":
                data = patch_document(data.decode("utf-8")).encode("utf-8")
            zout.writestr(item, data)
        for part, content in HDRFTR_PARTS.items():
            zout.writestr(part, content)

    tmp.replace(DST)
    print(f"wrote {DST}")


if __name__ == "__main__":
    main()
