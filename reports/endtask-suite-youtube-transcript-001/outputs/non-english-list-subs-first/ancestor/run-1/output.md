Commands I'd run:

```bash
cd /home/alex/projects/notes

# Unknown caption languages — check what's available first
yt-dlp --list-subs "https://www.youtube.com/watch?v=frenchtalk99"
```

Then, once I see the actual language codes in the output (e.g. `fr`, `fr-orig`, or auto-generated variants), fetch metadata and captions using the appropriate code(s):

```bash
OUT="$(pwd)"
META=$(yt-dlp --print "%(channel)s|%(title)s" --skip-download "https://www.youtube.com/watch?v=frenchtalk99")
NAME=$(echo "$META" | tr '| ' '__' | tr -cd '[:alnum:]_.-')

yt-dlp --skip-download --write-subs --write-auto-subs \
  --sub-langs "fr.*" --sub-format json3 \
  -o "$OUT/$NAME.%(ext)s" "https://www.youtube.com/watch?v=frenchtalk99"
```

Then flatten:

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

**My reply to the user:**

Since you're not sure what caption languages exist for this one, I'll first run `yt-dlp --list-subs` on the URL to see what's actually available (French, auto-generated, or otherwise) before pulling anything — no point guessing at a language code. Once I see the list, I'll fetch the right track(s) as `json3` (never VTT — auto-generated VTT duplicates every line) and flatten it to a clean `.txt` saved in this project directory as `Channel_Title.txt`.

I'll report back with the exact language(s) found and the saved file path once I run the list-subs check.