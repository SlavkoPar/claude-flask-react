import { Fragment } from 'react'

// PDF-derived document content is stored/returned as JSON `{"filename", "pages":
// [...]}`; documents created directly hold plain text. Returns the text to
// display or edit either way — real `\n`s instead of a one-line JSON blob.
export function extractDisplayText(content) {
  try {
    const parsed = JSON.parse(content)
    if (parsed && typeof parsed === 'object' && Array.isArray(parsed.pages)) {
      return parsed.pages.join('\n\n')
    }
  } catch {
    // not JSON — plain text content
  }
  return content
}

// Renders `\n`-separated text as <br>-separated lines, collapsing other
// runs of whitespace (PDF extraction leaves stray spaces/tabs) to one space.
export function withLineBreaks(text) {
  return text
    .split(/\n+/)
    .map(line => line.replace(/\s+/g, ' ').trim())
    .filter(Boolean)
    .map((line, i) => (
      <Fragment key={i}>
        {i > 0 && <br />}
        {line}
      </Fragment>
    ))
}
