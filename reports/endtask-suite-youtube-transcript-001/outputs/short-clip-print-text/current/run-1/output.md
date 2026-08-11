Fetching the transcript for that video now.

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

If the channel metadata comes back null, fall back to `uploader` then `uploader_id` for the filename. If captions fail to fetch, run `yt-dlp --list-subs "https://www.youtube.com/watch?v=short60sec"` to check available languages before retrying with an adjusted `--sub-langs`. If yt-dlp is out of date, run `yt-dlp -U` once and retry once, then stop. If the fetch returns a 429 or "Sign in to confirm you're not a bot" error, I'll stop immediately rather than retry, since that means the IP is flagged and retrying makes it worse.

Once I have the file, I'll save it to /home/alex/projects/quotes as `Channel_Title.txt` (spaces replaced with underscores), report the saved path, and since a 58-second clip should produce a very short transcript, I'll print the full text here too (under ~500 words).