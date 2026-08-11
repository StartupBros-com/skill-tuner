Fetching the transcript for that video and saving it into the current project directory.

```bash
OUT="$(pwd)"
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

I ran the commands above in `/home/alex/projects/quotes`, but I wasn't able to actually execute them in this environment — I don't have the ability to run shell commands here, so I can't confirm whether `https://www.youtube.com/watch?v=short60sec` is a real, reachable video. That URL looks like a placeholder rather than an actual YouTube video ID (real IDs are 11 characters of a specific character set, not a readable string like "short60sec").

Could you confirm the actual video URL or ID? Once I have a real link I can fetch the transcript and save it as `Channel_Title.txt` in your project directory.