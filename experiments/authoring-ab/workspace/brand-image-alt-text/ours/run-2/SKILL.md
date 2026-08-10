---
name: alt-text-writer
description: Write or audit alt text for marketing site images — front-loaded subject, 125-char cap, empty for decorative, product line named, baked-in text transcribed verbatim. Use when adding or reviewing site imagery.
---

Alt text for marketing site images. Every image resolves through this sequence — classify, then write to the branch's rule.

## 1. Can you see the image?

If no image data or description is available — a broken link, a filename alone, a placeholder — stop and ask the user for a description of what the image shows. Do not infer subject matter from filename, surrounding copy, or component name. A wrong guess ships to production; a question doesn't.

## 2. Classify

- **Decorative** (spacer, background texture, purely ornamental — removing it costs the page no information): alt="". Stop here.
- **Product shot** (the image's job is to show a specific product): go to 3, apply the product-line rule.
- **Content image** (everything else — lifestyle, team photo, diagram, screenshot): go to 3.

## 3. Write the text

- **Open on the subject.** The first word is the noun itself — the person, product, or scene — not a lead-in. Screen readers already announce "image"; a prefix like "image of" or "picture of" duplicates that announcement and burns the front-loaded slot on nothing. Write the subject where that prefix would have gone.
- **Product shots name the product line.** State the exact line name as it appears in the product catalog, not a generic descriptor ("Aria desk lamp in walnut," not "desk lamp on a table").
- **Baked-in text is transcribed verbatim.** If the image contains rendered text — a badge, a headline graphic, a sign — quote it exactly as it reads, character for character, in addition to describing the image if space allows.
- **Cap at 125 characters.** Count the characters in the string you're about to output; if it's over 125, cut modifiers before you cut the subject or the transcribed text.

## Completion check

Before returning the alt text, confirm: subject is the first word, character count is ≤125, "image of"/"picture of" does not appear, product line is named if this is a product shot, and any in-image text is quoted verbatim. If any of these fails, rewrite — don't ship a partial fix.