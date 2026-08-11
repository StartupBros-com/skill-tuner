---
name: youtube-transcript
description: Use whenever the user needs the transcript of a YouTube video — fetching, extracting, downloading, or pulling captions/subtitles/transcript text from a YouTube URL via yt-dlp. Triggers on "get the transcript", "transcript of this video", "pull the captions", "download subtitles".
disable-model-invocation: true
---

<!--
  Adapted from davidondrej/skills (MIT) — LICENSE + UPSTREAM.md in this
  directory carry full attribution. ALL DeepAPI content stripped (paid
  third-party path we don't subscribe to); this is the yt-dlp fallback
  standing alone. disable-model-invocation SET (upstream had it
  model-invocable): content is thin without the vendor path, and grep found
  zero existing transcript-fetching workflow in this harness to justify an
  always-on trigger — invoke explicitly with `/youtube-transcript` instead.
  Revisit if usage shows this recurring.
-->

# YouTube Transcript (yt-dlp)

Fetch a YouTube video's transcript and save a clean raw `.txt` file via `yt-dlp` captions — no third-party API, everything below runs locally.

## Save location
- If the user is in a real project/working dir → save there.
- Otherwise (no dir given, or cwd makes no sense) → save to `~/Downloads`.
- **Always name the file `Channel_Title` with spaces replaced by `_`** (e.g. `David_Ondrej_title_of_video.txt`). If metadata is unavailable, fall back to the video ID.

## Fetch captions

```bash
OUT="$(pwd)"            # or ~/Downloads if cwd makes no sense
META=$(yt-dlp --print "%(channel)s|%(title)s" --skip-download "URL")
NAME=$(echo "$META" | tr '| ' '__' | tr -cd '[:alnum:]_.-')   # "Channel_Title", spaces -> _, strip unsafe chars
yt-dlp --skip-download --write-subs --write-auto-subs \
  --sub-langs "en.*" --sub-format json3 \
  -o "$OUT/$NAME.%(ext)s" "URL"
```

- Fall back `channel` → `uploader` → `uploader_id` if `channel` is null.
- `--skip-download` = captions only. `--write-subs` + `--write-auto-subs` = manual first, auto as fallback.
- **Always use `json3`, never VTT/SRT** — auto VTT repeats every line twice (rolling captions).

## Flatten json3 → raw text

```bash
python3 - "$OUT" <<'PY'
import json, html, re, glob, sys, pathlib
f = glob.glob(sys.argv[1] + "/*.json3")
if not f: sys.exit("no json3 file")
data = json.load(open(f[0], encoding="utf-8"))
parts = ["".join(s.get("utf8","") for s in e.get("segs") or []) for e in data.get("events", [])]
txt = re.sub(r"\s+", " ", html.unescape(" ".join(p.strip() for p in parts if p.strip()))).strip()
out = pathlib.Path(f[0]).with_suffix(".txt")
out.write_text(txt, encoding="utf-8"); print(out)
PY
```

## Failure handling

- Non-English / unknown language: run `yt-dlp --list-subs "URL"` first, then set `--sub-langs`.
- Newer yt-dlp may need `deno` on PATH for YouTube extraction.
- On first failure: run `yt-dlp -U` once, retry once, then stop.
- **429 / "Sign in to confirm you're not a bot"** = IP flagged. STOP — do NOT retry in a loop (makes it worse).
- Never fall back to downloading audio for Whisper unless the user explicitly asks.

## Output

Report the saved path; print the text if short.
