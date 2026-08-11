OUT="/home/alex/media/transcripts/keynote"
META=$(yt-dlp --print "%(channel)s|%(title)s" --skip-download "https://www.youtube.com/watch?v=abc123DEF45")
NAME=$(echo "$META" | tr '| ' '__' | tr -cd '[:alnum:]_.-')
yt-dlp --skip-download --write-subs --write-auto-subs \
  --sub-langs "en.*" --sub-format json3 \
  -o "$OUT/$NAME.%(ext)s" "https://www.youtube.com/watch?v=abc123DEF45"

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

The final .txt file ends up in /home/alex/media/transcripts/keynote/, named Channel_Title.txt (channel and title pulled from the video's metadata, spaces replaced with underscores), not in /home/alex/scratch/tmp-2024-08.