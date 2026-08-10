---
name: alt-text-writer
description: Writing alt text for marketing site images — when adding new images or reviewing/auditing existing site imagery. Enforces subject-first phrasing, the 125-char cap, decorative/product/text-transcription rules; refuses to guess content it cannot see.
---

Writes alt text for marketing site images. Applies every time an image is added or existing alt text is reviewed.

## 1. Confirm you can see the image

Before writing anything, check that the image's actual content is in front of you — not just a filename, a caption, or surrounding copy. A filename never stands in for the image.

If you cannot see it, stop and ask the user for a description. Do not infer subject, mood, or setting from context. Done when either the image itself or a user-supplied description is in hand — not before.

## 2. Classify: decorative or meaningful

**Decorative** — carries no information the page doesn't already convey elsewhere (dividers, background textures, generic filler photography). Alt text: `alt=""`. Stop here; skip step 3.

**Meaningful** — everything else, including product shots and any image containing text. Continue to step 3.

If it's unclear which one applies, ask rather than defaulting to either.

## 3. Compose the alt text

Write a draft, then check it against every rule below before treating it as done:

- **Subject-first.** Lead with what's actually in the image — the person, object, or action — not scene-setting ("Sunset over the bay" not "A photo taken at sunset showing the bay").
- **No `image of` / `picture of` / `photo of`.** The alt attribute already signals it's an image; naming the medium is dead weight.
- **Product shots name the product line.** "Trailrunner 3 hiking boot," not "hiking boot" or "shoe." If you can't identify which product line is shown, ask — don't substitute a generic term.
- **Baked-in text is transcribed verbatim.** Labels, signage, on-screen text, captions rendered into the image itself — copy them exactly, don't paraphrase or summarize. If the text is illegible, ask rather than guessing at it.
- **125 characters max**, counted including spaces. Trim by cutting scene-setting first, never by dropping the product line or baked-in text.

Done when the draft satisfies all five rules on a re-read — not on the first pass that merely mentions the subject.