Since the caption language is unknown, I'll list available subs first, then fetch based on what's actually there.

```bash
yt-dlp --list-subs "https://www.youtube.com/watch?v=frenchtalk99"
```

Based on the listing, pick the right language code(s) (likely `fr.*`, but I'll confirm from the actual output rather than assume) and fetch:

```bash
OUT="/home/alex/projects/notes"
META=$(yt-dlp --print "%(channel)s|%(title)s" --skip-download "https://www.youtube.com/watch?v=frenchtalk99")
NAME=$(echo "$META" | tr '| ' '__' | tr -cd '[:alnum:]_.-')
yt-dlp --skip-download --write-subs --write-auto-subs \
  --sub-langs "fr.*" --sub-format json3 \
  -o "$OUT/$NAME.%(ext)s" "https://www.youtube.com/watch?v=frenchtalk99"
```

Then flatten:

```bash
python3 - "/home/alex/projects/notes" <<'PY'
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

Since I don't know yet what caption languages this video actually has, I'll start by running `yt-dlp --list-subs` on it to see what's available (French, English auto-captions, etc.). Once I see the real list, I'll grab the right one — captions in French are fine, I'll just set `--sub-langs` to match whatever code actually shows up rather than guessing `fr.*` blind. I'll save the result into your `notes` project dir as `json3` (never VTT, since auto-generated VTT duplicates lines) and then flatten it to a clean `.txt` file named `Channel_Title.txt`. I'll report back with the saved path once it's done — if it turns out there's no French track at all, I'll flag that before pulling whatever fallback language does exist.