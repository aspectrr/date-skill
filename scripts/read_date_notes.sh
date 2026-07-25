#!/usr/bin/env bash
# Dumps Apple Notes date-related notes as clean text.
# Reads: Dates, Restaurants to visit, Date Fund
# Source of ideas + wishlist + spend history (what's already done).
set -euo pipefail

dump_one() {
  # $1 = exact note title. Returns HTML body or empty.
  osascript <<EOF 2>/dev/null
tell application "Notes"
  try
    set n to the first note whose name is "$1"
    return (body of n)
  on error
    return ""
  end try
end tell
EOF
}

strip_html() {
  # Notes body is simple HTML; turn block tags into newlines, drop the rest.
  sed -E -e 's#<br>#\n#g' \
         -e 's#</?(li|h[0-9]|p|div)>#\n#g' \
         -e 's#<[^>]*>##g' \
         -e 's/&amp;/\&/g' -e 's/&nbsp;/ /g' -e 's/&#39;/'"'"'/g'
}

trim_blanks() { sed -E '/^[[:space:]]*$/d'; }

for title in "Dates" "Restaurants to visit" "Date Fund"; do
  echo "=== $title ==="
  dump_one "$title" | strip_html | trim_blanks
  echo
done
