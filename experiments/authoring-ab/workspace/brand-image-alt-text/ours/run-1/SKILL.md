---
name: alt-text-writer
description: Writes and reviews alt text for marketing site images — use whenever site imagery is added or existing alt text is reviewed.
---

Alt text on the marketing site follows one shape: subject first, plain language, under the character ceiling. This document is the reference for producing or auditing it.

## The ceiling

125 characters, hard ceiling. Count the characters before finishing — a string at 126 fails the same as a string at 200. This is not a target to approach; text that could say more in fewer characters should.

## Lead with the subject

The first word is what's depicted, not a description of the depiction. State the subject directly — never prefix with "image of" or "picture of." A screen reader already announces "image"; prefixing it again wastes the front of the string, the position most likely to survive truncation.

- Wrong: "Image of a woman using a laptop on a park bench"
- Right: "Woman using a laptop on a park bench"

## Decorative images

If an image carries no information — a background texture, a spacer, a purely stylistic flourish — its alt attribute is `alt=""`, empty, not omitted and not filled with a description. An empty alt on a decorative image is correct, not incomplete; do not pad it to look more thorough.

## Product shots

Any image whose subject is a product names the product line in the alt text. "Blue running shoe" is not enough if the product line is "Aria Trail Runner" — the line name is the fact a screen-reader user cannot infer from a generic noun phrase, and it's the fact most likely to matter to them (matching what they searched for, confirming what's in their cart).

## Text baked into the image

If the image contains rendered text — a banner graphic, a screenshotted quote, a badge — transcribe that text verbatim inside the alt attribute. Don't summarize or paraphrase it; a screen-reader user reading the alt text should get the same words a sighted user reads off the image. If the baked-in text alone would exceed the ceiling, transcribe as much as fits and prioritize the words a user would need to act (a CTA, a price, a warning) over decorative framing.

## When you can't see the image

If the image file isn't visible to you — a broken link, a placeholder, a reference to an asset not in context — do not guess at its content from the filename, surrounding copy, or prior similar images. Ask the person for a plain-language description of what's depicted, then write the alt text from that description. Alt text invented from a guess is worse than no alt text: it actively misinforms the person relying on it.