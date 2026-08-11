Since the caption languages are unknown, I'll list available subtitles first, then fetch based on what's actually there.

```bash
cd /home/alex/projects/notes

# 1. Check what caption languages/tracks actually exist
yt-dlp --list-subs "https://www.youtube.com/watch?v=frenchtalk99"
```

Based on the output of `--list-subs`, pick the right language code(s) (e.g. `fr`, `fr-FR`, or whatever auto-caption variant shows up) and continue:

```bash
OUT="$(pwd)"
META=$(yt-dlp --print "%(channel)s|%(title)s" --skip-download "https://www.youtube.com/watch?v=frenchtalk99")
NAME=$(echo "$META" | tr '| ' '__' | tr -cd '[:alnum:]_.-')

yt-dlp --skip-download --write-subs --write-auto-subs \
  --sub-langs "fr.*" --sub-format json3 \
  -o "$OUT/$NAME.%(ext)s" "https://www.youtube.com/watch?v=frenchtalk99"
```

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

---

Since you weren't sure what caption languages are available, I'll start by running `yt-dlp --list-subs` on that URL — that'll show every manual and auto-generated track it has (French, English, whatever). Once I see the real language codes, I'll fetch captions using `json3` format (never VTT/SRT, since auto VTT duplicates lines), saved into your `notes` project dir as `Channel_Title.txt`, then flatten it to plain text and share the path (and the text itself if it's short).

I haven't run anything yet since I need the actual `--list-subs` output to pick the right language code — want me to go ahead and run it?