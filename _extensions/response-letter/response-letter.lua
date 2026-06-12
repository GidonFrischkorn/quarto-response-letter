--[[
response-letter.lua

Transforms four fenced divs into styled blocks across PDF, DOCX, and HTML:

  ::: {.comment}  -- a reviewer comment (auto-numbered "Comment R.C")
  ::: {.reply}    -- the authors' reply
  ::: {.changes}  -- list of manuscript changes
  ::: {.quoted loc="..."} -- verbatim quote from the revised manuscript

Numbering: every level-1 header increments the reviewer counter and resets
the comment counter; every .comment div increments the comment counter and
receives the identifier #cmt-R-C (unless the author set one), so
"see [Comment 1.2](#cmt-1-2)" works in all formats.

The label is injected as a bold first paragraph inside the box, so all
three formats show identical labels. Output mapping:
  latex -> tcolorbox environments defined in header.tex
  docx  -> custom-style paragraph styles defined in reference.docx
  html  -> the div classes themselves, styled by response-letter.css
]]

local labels = {
  comment = "Comment",
  reply   = "Reply",
  changes = "Changes",
  quoted  = "Manuscript",
}

local latex_env = {
  comment = "CommentBox",
  reply   = "ReplyBox",
  changes = "ChangesBox",
  quoted  = "QuoteBox",
}

local docx_style = {
  comment = "Response Comment",
  reply   = "Response Reply",
  changes = "Response Changes",
  quoted  = "Response Quote",
}

local DOCX_LABEL_STYLE = "Response Label"

local reviewer_n = 0
local comment_n  = 0

local is_latex = FORMAT:match("latex")
local is_docx  = FORMAT:match("docx")

local stringify = pandoc.utils.stringify

local function read_labels(meta)
  local lang = meta.language
  if not lang then return end
  local keys = {
    comment = "response-comment-label",
    reply   = "response-reply-label",
    changes = "response-changes-label",
    quoted  = "response-quoted-label",
  }
  for kind, key in pairs(keys) do
    if lang[key] then labels[kind] = stringify(lang[key]) end
  end
end

local function label_text(kind, div)
  if kind == "comment" then
    return string.format("%s %d.%d", labels.comment, reviewer_n, comment_n)
  elseif kind == "quoted" then
    local loc = div.attributes["loc"]
    if loc and loc ~= "" then
      return string.format("%s (%s):", labels.quoted, loc)
    end
    return labels.quoted .. ":"
  end
  return labels[kind] .. ":"
end

local function label_block(kind, text)
  local para = pandoc.Para({ pandoc.Strong({ pandoc.Str(text) }) })
  if is_docx then
    return pandoc.Div({ para },
      pandoc.Attr("", {}, { ["custom-style"] = DOCX_LABEL_STYLE }))
  end
  local div = pandoc.Div({ para })
  div.classes = { "box-label", "box-label-" .. kind }
  return div
end

local kind_of, transform  -- forward declarations

-- Recursively transform known divs inside a block list (e.g., a .quoted
-- div nested inside a .reply div). Also drives the reviewer counter.
local function walk_blocks(blocks)
  local out = pandoc.List()
  for _, block in ipairs(blocks) do
    if block.t == "Header" and block.level == 1 then
      reviewer_n = reviewer_n + 1
      comment_n = 0
      out:insert(block)
    elseif block.t == "Div" and kind_of(block) then
      out:extend(transform(block))
    else
      out:insert(block)
    end
  end
  return out
end

kind_of = function(div)
  for _, kind in ipairs({ "comment", "reply", "changes", "quoted" }) do
    if div.classes:includes(kind) then return kind end
  end
  return nil
end

transform = function(div)
  local kind = kind_of(div)
  if kind == "comment" then
    comment_n = comment_n + 1
    if div.identifier == "" then
      div.identifier = string.format("cmt-%d-%d", reviewer_n, comment_n)
    end
  end

  local content = walk_blocks(div.content)
  content:insert(1, label_block(kind, label_text(kind, div)))

  if is_latex then
    local blocks = pandoc.List()
    if div.identifier ~= "" then
      -- Empty span carries the link target; pandoc emits the anchor
      -- syntax matching its own internal-link output.
      blocks:insert(pandoc.Plain({
        pandoc.Span({}, pandoc.Attr(div.identifier))
      }))
    end
    blocks:insert(pandoc.RawBlock("latex",
      "\\begin{" .. latex_env[kind] .. "}"))
    blocks:extend(content)
    blocks:insert(pandoc.RawBlock("latex",
      "\\end{" .. latex_env[kind] .. "}"))
    return blocks
  end

  if is_docx then
    local styled = pandoc.Div(content,
      pandoc.Attr(div.identifier, {}, { ["custom-style"] = docx_style[kind] }))
    return pandoc.List({ styled })
  end

  -- html and everything else: keep the class, let CSS do the work
  div.content = content
  return pandoc.List({ div })
end

function Pandoc(doc)
  read_labels(doc.meta)
  doc.blocks = walk_blocks(doc.blocks)
  return doc
end
