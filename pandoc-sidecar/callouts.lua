-- Lua filter: remap pandoc's native GFM alert divs to our callout classes,
-- and add emoji icons to the title.
--
-- Pandoc 3.x converts > [!NOTE] etc. into:
--   <div class="note"><div class="title"><p>Note</p></div>...</div>
--
-- We remap to:
--   <div class="callout callout-note">
--     <p><span class="callout-title">ℹ️ Note</span></p>
--     ...
--   </div>

local types = {
  note      = { label = "Note",      icon = "\u{2139}\u{FE0F}" },
  tip       = { label = "Tip",       icon = "\u{1F4A1}" },
  important = { label = "Important", icon = "\u{1F4CC}" },
  warning   = { label = "Warning",   icon = "\u{26A0}\u{FE0F}" },
  caution   = { label = "Caution",   icon = "\u{1F534}" },
}

function Div(el)
  -- Match pandoc's native alert classes: "note", "tip", etc.
  for _, cls in ipairs(el.classes) do
    local info = types[cls]
    if info then
      -- Remove the native .title div if present; we build our own title
      local blocks = {}

      -- Title line
      table.insert(blocks, pandoc.Para({
        pandoc.Span(
          { pandoc.Str(info.icon .. " " .. info.label) },
          pandoc.Attr("", { "callout-title" })
        )
      }))

      -- Copy remaining blocks, skipping the .title div
      for _, block in ipairs(el.content) do
        if block.t == "Div" then
          local is_title = false
          for _, c in ipairs(block.classes) do
            if c == "title" then is_title = true end
          end
          if not is_title then
            table.insert(blocks, block)
          end
        else
          table.insert(blocks, block)
        end
      end

      return pandoc.Div(blocks, pandoc.Attr("", { "callout", "callout-" .. cls }))
    end
  end
end
