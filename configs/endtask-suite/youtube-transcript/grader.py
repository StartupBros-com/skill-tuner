#!/usr/bin/env python3
"""Deterministic grader for the youtube-transcript skill end-task A/B.

Invocation (per the endtask grader contract):
    python3 grader.py <output_file> <case_id> <condition>

Prints ONLY a JSON object: {"pass_rate": float in [0,1], "expectations": [...]}.
Python 3 stdlib only. Never raises; always exits 0. `condition` is accepted
for logging only and never referenced in grading logic -- both conditions
are graded by the identical rules below.
"""

from __future__ import annotations

import json
import re
import sys

CORE_FLAGS = ("--skip-download", "--write-subs", "--write-auto-subs", "--sub-format json3")


def core_flags_present(text: str) -> bool:
    return all(flag in text for flag in CORE_FLAGS)


def naming_convention_present(text: str) -> bool:
    # Require BOTH channel and title (not either alone) -- the skill's
    # naming rule is "Channel_Title" jointly, not just the video title.
    both_tokens = "%(channel)s" in text and "%(title)s" in text
    explicit_literal = bool(re.search(
        r"Channel_Title"
        r"|channel.{0,15}title.{0,30}underscore"
        r"|underscore.{0,30}channel.{0,15}title"
        r"|spaces?.{0,20}(replaced|converted).{0,20}underscore.{0,40}channel",
        text, re.I,
    ))
    return both_tokens or explicit_literal


# ---------------------------------------------------------------------------
# Case 1: explicit_output_dir -- user names a dir different from cwd; it
# must win over both cwd and the ~/Downloads default.
# ---------------------------------------------------------------------------
def check_explicit_output_dir(text: str) -> list[tuple[str, bool]]:
    explicit_dir = "/home/alex/media/transcripts/keynote"
    scratch_dir = "/home/alex/scratch/tmp-2024-08"
    scratch_used_as_out = bool(re.search(
        r'(OUT\s*=\s*"?' + re.escape(scratch_dir) + r'|-o\s+"?' + re.escape(scratch_dir) + r')',
        text,
    ))
    out_target_is_explicit = bool(re.search(r'OUT\s*=\s*"?' + re.escape(explicit_dir), text)) or \
        bool(re.search(r'-o\s+"?' + re.escape(explicit_dir), text))
    o_flag_wired = bool(re.search(r'-o\s+"?\$\{?OUT\}?/', text)) or \
        bool(re.search(r'-o\s+"?' + re.escape(explicit_dir), text))
    return [
        ("OUT is set to the explicit dir the user named", out_target_is_explicit),
        ("does not save into the cwd (scratch dir) instead", not scratch_used_as_out),
        ("does not default to ~/Downloads when an explicit dir was given",
         not bool(re.search(r"~/Downloads|\$HOME/Downloads", text))),
        ("core yt-dlp capture flags present", core_flags_present(text)),
        ("-o flag present and wired to the output location", o_flag_wired),
    ]


# ---------------------------------------------------------------------------
# Case 2: nonsensical_cwd_root -- cwd is "/"; must route to ~/Downloads, not
# write into the filesystem root.
# ---------------------------------------------------------------------------
def check_nonsensical_cwd_root(text: str) -> list[tuple[str, bool]]:
    falls_back_downloads = bool(re.search(r"~/Downloads|\$HOME/Downloads|/Downloads\b", text))
    root_output = bool(re.search(r'-o\s+"?/\$\{?NAME|OUT\s*=\s*"/"\s*(\n|$)|-o\s+"/', text, re.M))
    saves_in_cwd_wrongly = bool(re.search(
        r"(save|saved|saving|writ(e|ing)).{0,40}(current directory|cwd|current folder|current working directory)",
        text, re.I,
    )) and not falls_back_downloads
    bare_pwd_unadapted = (
        bool(re.search(r'OUT\s*=\s*"?\$\(pwd\)"?', text))
        and not falls_back_downloads
    )
    return [
        ("falls back to ~/Downloads since cwd (/) makes no sense", falls_back_downloads),
        ("does not write output at the filesystem root", not root_output),
        ("does not save into the current dir (root) instead of Downloads",
         not saves_in_cwd_wrongly and not bare_pwd_unadapted),
        ("core yt-dlp capture flags present", core_flags_present(text)),
        ("channel/title naming convention (or ID fallback) preserved",
         naming_convention_present(text) or bool(re.search(r"video\s*id|%\(id\)s", text, re.I))),
    ]


# ---------------------------------------------------------------------------
# Case 3: very_long_transcript -- must report the saved path only, not dump
# the (very long) transcript text inline.
# ---------------------------------------------------------------------------
def check_very_long_transcript(text: str) -> list[tuple[str, bool]]:
    project_dir = "/home/alex/projects/course-notes"
    path_only_ack = bool(re.search(
        r"(only|just)\s+report(ing)?\s+(the\s+)?(saved\s+)?path"
        r"|report(ing)?\s+(the\s+)?(saved\s+)?path\s+(only|instead)"
        r"|won.?t\s+print|will\s+not\s+print"
        r"|not\s+print\s+(the\s+)?(full\s+)?(entire\s+)?text"
        r"|skip(ping)?\s+print(ing)?",
        text, re.I,
    ))
    mentions_saved_txt = bool(re.search(r"\.txt\b", text))
    return [
        ("reports the saved .txt path", mentions_saved_txt),
        ("explicitly states it will NOT print the full transcript (too long)", path_only_ack),
        ("uses the real project cwd rather than ignoring it", project_dir in text),
        ("core yt-dlp capture flags present", core_flags_present(text)),
        ("does not default to ~/Downloads despite a legitimate project cwd",
         not bool(re.search(r"~/Downloads|\$HOME/Downloads", text))),
    ]


# ---------------------------------------------------------------------------
# Case 4: short_clip_print_text -- short clip, must print the flattened text.
# ---------------------------------------------------------------------------
def check_short_clip_print_text(text: str) -> list[tuple[str, bool]]:
    project_dir = "/home/alex/projects/quotes"
    prints_text = bool(re.search(
        r"print(ing)?\s+(the\s+)?(full\s+)?(transcript\s+)?text"
        r"|display(ing)?\s+(the\s+)?(transcript|text)"
        r"|show(ing)?\s+(the\s+)?(transcript\s+)?text"
        r'|cat\s+"?\$?\{?OUT|print\(txt\)',
        text, re.I,
    ))
    wrongly_path_only = bool(re.search(
        r"(only|just)\s+report(ing)?\s+(the\s+)?(saved\s+)?path"
        r"|report(ing)?\s+(the\s+)?(saved\s+)?path\s+(only|instead)",
        text, re.I,
    )) and not prints_text
    flatten_logic = bool(re.search(r"json3|flatten", text, re.I))
    return [
        ("core yt-dlp capture flags present", core_flags_present(text)),
        ("uses the real project cwd", project_dir in text),
        ("prints/displays the transcript text since the clip is short", prints_text),
        ("does not wrongly withhold text as path-only for a short clip", not wrongly_path_only),
        ("includes json3-flatten logic to produce printable text", flatten_logic),
    ]


# ---------------------------------------------------------------------------
# Case 5: yt_dlp_invocation_correctness -- command-shape + no DeepAPI/paid path.
# ---------------------------------------------------------------------------
def check_yt_dlp_invocation_correctness(text: str) -> list[tuple[str, bool]]:
    bad_api_call = bool(re.search(
        r"deepapi|curl\s+.*api\.|requests\.post\(|POST\s+https?://api",
        text, re.I,
    ))
    return [
        ("invokes yt-dlp", "yt-dlp" in text),
        ("uses --skip-download (captions only, no video)", "--skip-download" in text),
        ("requests both manual and auto subs", "--write-subs" in text and "--write-auto-subs" in text),
        ("uses json3 sub format (not vtt/srt)", "--sub-format json3" in text),
        ("scopes sub language with --sub-langs", "--sub-langs" in text),
        ("no third-party/DeepAPI transcript call", not bad_api_call),
        ("channel/title naming convention present", naming_convention_present(text)),
    ]


# ---------------------------------------------------------------------------
# Case 6: rate_limit_429_stop -- 429/bot-check must halt, not retry-loop or
# silently fall back to Whisper audio transcription.
# ---------------------------------------------------------------------------
def check_rate_limit_429_stop(text: str) -> list[tuple[str, bool]]:
    identifies_situation = bool(re.search(
        r"\b429\b|rate.?limit(ed)?|flagged|not a bot|sign in to confirm", text, re.I,
    ))
    says_stop_no_retry = bool(re.search(
        r"don.?t retry|do not retry|stop\b[^.]{0,40}retry|avoid retry|should not retry|won.?t retry"
        r"|no automatic retry|do not loop",
        text, re.I,
    ))
    # Structural/unambiguous phrasing only -- "do not retry in a loop" (the
    # correct advice) must NOT trip this; only an actual proposed loop should.
    retry_loop_proposed = bool(re.search(
        r"while\s+true|for\s+i\s+in\s+.{0,10}(seq|range)|keep retrying"
        r"|try again and again|retry(ing)? until it (works|succeeds)",
        text, re.I,
    ))
    whisper_mentioned = bool(re.search(r"whisper", text, re.I))
    whisper_gated = whisper_mentioned and bool(re.search(
        r"unless.{0,60}(ask|explicit)|only if.{0,60}(ask|explicit)|explicitly ask", text, re.I,
    ))
    return [
        ("identifies this as an IP-flag/rate-limit situation", identifies_situation),
        ("explicitly says to stop rather than auto-retry", says_stop_no_retry),
        ("does not propose a retry loop", not retry_loop_proposed),
        ("does not silently fall back to Whisper audio transcription",
         (not whisper_mentioned) or whisper_gated),
    ]


# ---------------------------------------------------------------------------
# Case 7: non_english_list_subs_first -- uncertain caption language must be
# checked with --list-subs before blindly fetching English.
# ---------------------------------------------------------------------------
def check_non_english_list_subs_first(text: str) -> list[tuple[str, bool]]:
    project_dir = "/home/alex/projects/notes"
    uses_list_subs = "--list-subs" in text
    adjusts_lang = bool(re.search(r"\bfr\b|\bfrench\b|based on (the )?(list-subs|available)", text, re.I))
    return [
        ("checks available caption languages first (--list-subs)", uses_list_subs),
        ("does not blindly hardcode English-only without checking",
         uses_list_subs or adjusts_lang),
        ("core yt-dlp capture flags present", core_flags_present(text)),
        ("uses the real project cwd", project_dir in text),
    ]


CASES = {
    "explicit-output-dir": check_explicit_output_dir,
    "nonsensical-cwd-root": check_nonsensical_cwd_root,
    "very-long-transcript-path-only": check_very_long_transcript,
    "short-clip-print-text": check_short_clip_print_text,
    "yt-dlp-invocation-correctness": check_yt_dlp_invocation_correctness,
    "rate-limit-429-stop": check_rate_limit_429_stop,
    "non-english-list-subs-first": check_non_english_list_subs_first,
}


def main() -> None:
    try:
        output_path = sys.argv[1]
        case_id = sys.argv[2]
        # sys.argv[3] is `condition` -- accepted for logging only, never
        # referenced in grading logic (both conditions graded identically).
        try:
            with open(output_path, "r", encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        except OSError:
            text = ""

        check_fn = CASES.get(case_id)
        if check_fn is None:
            print(json.dumps({"pass_rate": 0.0, "expectations": []}))
            return

        results = check_fn(text)
        # An output that never even invokes yt-dlp hasn't attempted the task
        # at all (every valid answer in this domain references the tool at
        # least once) -- force zero credit rather than letting vacuous
        # "does-not-do-the-wrong-thing" checks pass on empty/off-topic text.
        # Exception: rate-limit-429-stop is a pure advice reply to an error
        # that already happened -- the prompt never asks for commands, so a
        # fully correct answer need not say "yt-dlp" literally. Gate that
        # case on topical engagement (mentions the error/situation) instead,
        # so it still zeroes out empty/off-topic text without falsely
        # zeroing a valid on-topic reply.
        engaged = "yt-dlp" in text.lower()
        if case_id == "rate-limit-429-stop":
            engaged = engaged or bool(re.search(
                r"\b429\b|rate.?limit|flagged|not a bot|sign in to confirm", text, re.I,
            ))
        expectations = [{"name": name, "ok": bool(ok) and engaged} for name, ok in results]
        total = len(expectations)
        passed = sum(1 for e in expectations if e["ok"])
        pass_rate = (passed / total) if total else 0.0
        print(json.dumps({"pass_rate": pass_rate, "expectations": expectations}))
    except Exception as exc:  # never crash -- infra contract
        print(json.dumps({
            "pass_rate": 0.0,
            "expectations": [{"name": f"grader-error: {exc}", "ok": False}],
        }))


if __name__ == "__main__":
    main()
