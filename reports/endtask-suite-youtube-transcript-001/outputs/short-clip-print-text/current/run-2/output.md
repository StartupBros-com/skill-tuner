I'll fetch the transcript using yt-dlp, following the skill's steps: get channel/title metadata, download captions in json3 format, then flatten to plain text.

Commands:

```bash
OUT="/home/alex/projects/quotes"
META=$(yt-dlp --print "%(channel)s|%(title)s" --skip-download "https://www.youtube.com/watch?v=short60sec")
NAME=$(echo "$META" | tr '| ' '__' | tr -cd '[:alnum:]_.-')
yt-dlp --skip-download --write-subs --write-auto-subs \
  --sub-langs "en.*" --sub-format json3 \
  -o "$OUT/$NAME.%(ext)s" "https://www.youtube.com/watch?v=short60sec"
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

I attempted to fetch the transcript for that video, but it looks like `https://www.youtube.com/watch?v=short60sec` isn't a real/resolvable YouTube video ID — `yt-dlp` can't pull metadata or captions for it. Could you double-check the URL? If you paste the correct link, I'll grab the transcript right away.