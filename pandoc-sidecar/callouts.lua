-- Lua filter: convert GitHub-style alert blockquotes to styled divs.
-- Supports: > [!NOTE], [!TIP], [!IMPORTANT], [!WARNING], [!CAUTION]

local types = {
  NOTE      = { label = "Note",      icon = "\u{2139}\u{FE0F}" },
  TIP       = { label = "Tip",       icon = "\u{1F4A1}" },
  IMPORTANT = { label = "Important", icon = "\u{1F4CC}" },
  WARNING   = { label = "Warning",   icon = "\u{26A0}\u{FE0F}" },
  CAUTION   = { label = "Caution",   icon = "\u{1F534}" },
}

function BlockQuote(bq)
  if #bq.content == 0 then return end

  local first = bq.content[1]
  if first.t ~= "Para" or #first.content == 0 then return end
  if first.content[1].t ~= "Str" then return end

  local key = first.content[1].text:match("^%[!(%u+)%]$")
  if not key then return end

  local info = types[key]
  if not info then return end

  -- Build body inlines: everything after [!TYPE] and its following break
  local body_inlines = {}
  for i = 2, #first.content do
    local el = first.content[i]
    if i == 2 and (el.t == "LineBreak" or el.t == "SoftBreak") then
      -- skip the line break immediately after the marker
    else
      table.insert(body_inlines, el)
    end
  end

  local blocks = {}

  -- Title line
  table.insert(blocks, pandoc.Para({
    pandoc.Span(
      { pandoc.Str(info.icon .. " " .. info.label) },
      pandoc.Attr("", { "callout-title" })
    )
  }))

  -- Body from first para remainder
  if #body_inlines > 0 then
    table.insert(blocks, pandoc.Para(body_inlines))
  end

  -- Any additional blocks inside the blockquote
  for i = 2, #bq.content do
    table.insert(blocks, bq.content[i])
  end

  return pandoc.Div(blocks, pandoc.Attr("", { "callout", "callout-" .. key:lower() }))
end
