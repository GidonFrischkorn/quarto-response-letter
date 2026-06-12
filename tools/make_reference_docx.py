#!/usr/bin/env python3
"""Build _extensions/response-letter/reference.docx.

Takes pandoc's default reference.docx (pass its path as argv[1]) and injects
the five paragraph styles used by response-letter.lua. Re-run after pandoc
upgrades if the default reference doc changes:

    quarto pandoc --print-default-data-file reference.docx > /tmp/ref.docx
    python3 tools/make_reference_docx.py /tmp/ref.docx
"""
import shutil
import sys
import zipfile
from pathlib import Path

SRC = Path(sys.argv[1])
DST = Path(__file__).resolve().parent.parent / "_extensions/response-letter/reference.docx"

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

STYLES = LABEL + "".join(
    BOX.format(**s)
    for s in [
        dict(sid="ResponseComment", name="Response Comment",
             border="B22222", fill="FBF4F4", bsz="18", rpr="<w:rPr><w:i/></w:rPr>"),
        dict(sid="ResponseReply", name="Response Reply",
             border="1E90FF", fill="F6FAFF", bsz="18", rpr=""),
        dict(sid="ResponseChanges", name="Response Changes",
             border="8FBC8F", fill="F1F7F1", bsz="18", rpr=""),
        dict(sid="ResponseQuote", name="Response Quote",
             border="696969", fill="F5F5F5", bsz="24", rpr=""),
    ]
)

tmp = DST.with_suffix(".tmp.docx")
shutil.copy(SRC, tmp)

with zipfile.ZipFile(SRC) as zin:
    names = zin.namelist()
    styles = zin.read("word/styles.xml").decode("utf-8")

assert "ResponseComment" not in styles, "styles already injected"
styles = styles.replace("</w:styles>", STYLES + "</w:styles>")

with zipfile.ZipFile(SRC) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
    for name in names:
        data = styles.encode("utf-8") if name == "word/styles.xml" else zin.read(name)
        zout.writestr(name, data)

tmp.replace(DST)
print(f"Wrote {DST}")
