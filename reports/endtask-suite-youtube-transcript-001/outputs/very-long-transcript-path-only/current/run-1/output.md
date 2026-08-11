```bash
OUT="/home/alex/projects/course-notes"
META=$(yt-dlp --print "%(channel)s|%(title)s" --skip-download "https://www.youtube.com/watch?v=longlecture001")
NAME=$(echo "$META" | tr '| ' '__' | tr -cd '[:alnum:]_.-')
yt-dlp --skip-download --write-subs --write-auto-subs \
  --sub-langs "en.*" --sub-format json3 \
  -o "$OUT/$NAME.%(ext)s" "https://www.youtube.com/watch?v=longlecture001"
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

Transcript saved to `/home/alex/projects/course-notes/<Channel>_<Title>.txt`. Given the video is a 3-hour lecture, the transcript is several thousand words long, so I haven't printed it inline — open the file directly to view it.