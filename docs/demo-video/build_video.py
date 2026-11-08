"""Build the TrapTest demo video from the live run (6 Nov 2026).

Stills (PIL) + TTS narration per shot + burned captions.
v2 (8 Nov 2026): corrected re-score numbers (Truvian 4/12, strict
original 3/12), Shot 4 field fix, Shot 5 drawn corrected table,
receipt/signal hashes on Shot 3, verdict pulled before 0:60.
Output: traptest-demo-2026-11-08.mp4 (local only). v1 file
traptest-demo-2026-11-06.mp4 is NOT overwritten.

Narration text lives here AND in narration.md — keep them identical.
Run: python3 docs/demo-video/build_video.py
"""
import json
import subprocess
import sys
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
W, H = 1280, 720
BG = (14, 22, 38)
FG = (240, 244, 248)
MUTED = (160, 175, 195)
ACCENT = (96, 165, 250)
GREEN = (74, 222, 128)
RED = (248, 113, 113)
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONTB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONTM = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"

SHOTS = [
    {"key": "s1",
     "text": ("Telegraph ranks AI providers by intelligence. But who checks "
              "whether the ranking itself can be trusted? TrapTest does. It "
              "buys the same question from competing providers — a question "
              "whose answer is already known — and shows you who got it right."),
     "frame": "title"},
    {"key": "s2",
     "text": ("A trap is a transaction query with known ground truth. "
              "Its sender, recipient, value and block were checked "
              "against the public chain record before any provider "
              "was scored — so the truth never comes from a provider's own "
              "answer. Twelve traps like this were frozen on the 6th of "
              "November, before a single purchase was made."),
     "frame": "trap"},
    {"key": "s3",
     "text": ("Take one trap: a reverted transaction. TxLens answers: "
              "not found. It says that about every mined transaction we "
              "asked it. Truvian answers: reverted — with the right block, "
              "sender and recipient. Same question, same price. Different "
              "answers. TrapTest buys each trap from competing providers, "
              "one at a time, through Telegraph's Direct Ask. Every served "
              "call costs one cent of testnet USDC, and comes back with a "
              "signal hash and a Telegraph receipt — the evidence behind "
              "every scored row."),
     "frame": "compare"},
    {"key": "s4",
     "text": ("Scoring is strict. Status must match exactly — a wrong "
              "status fails the trap outright, and a missing field is a "
              "failure, never a pass. TxLens fails this trap on every "
              "scored field — it answered not found and returned nothing "
              "else. Truvian passes it outright. And here is the honest "
              "part. Truvian fails other traps, not because it got the "
              "transaction wrong — its block, sender, recipient and value "
              "were all right — but because it reports no status at all for "
              "confirmed transactions. Under strict scoring that is still a "
              "fail. We show the gap. We don't hide it, and we don't call "
              "it a lie."),
     "frame": "fields"},
    {"key": "s5",
     "text": ("Across all twelve traps, Truvian passed four, TxLens passed "
              "two — a corrected re-score; the strict original was three. "
              "Four versus two is two traps — evidence, not a verdict on "
              "provider quality. Three more providers couldn't serve this "
              "intent at all. LiveCert answered every call with a 503. "
              "Sigil and OnChain Intel failed upstream on all twelve — and "
              "those failed calls were not billed: twenty-four cents "
              "settled into Telegraph escrow credit instead. The "
              "leaderboard ranks on pass rate first, then traps run, then "
              "cost. A provider that returns a stale or wrong answer "
              "doesn't stay at the top."),
     "frame": "leaderboard"},
    {"key": "s6",
     "text": ("And a reviewer can repeat this. The trap set is frozen, the "
              "ground truth is public, and the same loop runs with a new "
              "trap input — receipts included. TrapTest doesn't ask you to "
              "trust a ranking. It shows you the receipts. TrapTest — "
              "Telegraph Hackathon Season Two. Testnet evaluation only. No "
              "independent adoption is claimed."),
     "frame": "reproduce"},
]


def font(size, bold=False, mono=False):
    return ImageFont.truetype(FONTM if mono else (FONTB if bold else FONT), size)


def draw_wrapped(d, xy, text, fnt, fill, width_chars=62, leading=8):
    x, y = xy
    for line in textwrap.wrap(text, width=width_chars):
        d.text((x, y), line, font=fnt, fill=fill)
        y += fnt.size + leading
    return y


def base():
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 10], fill=ACCENT)
    return im, d


def frame_title():
    im, d = base()
    d.text((80, 190), "TrapTest", font=font(110, bold=True), fill=FG)
    d.text((80, 330), "Who checks the ranking?", font=font(48), fill=ACCENT)
    d.text((80, 430), "Telegraph Hackathon Season II  ·  Evaluator track",
           font=font(28), fill=MUTED)
    return im


def frame_trap():
    im, d = base()
    d.text((80, 50), "One trap — known ground truth", font=font(44, bold=True), fill=FG)
    lines = [
        ("trap", "t01-plain-transfer"),
        ("intent", "ONCHAIN_TX_LOOKUP_GENERAL"),
        ("tx", "0xd47a09…ae96"),
        ("expected status", "confirmed"),
        ("from", "0xdead…0001"),
        ("to", "0x4200…0015"),
        ("value", "0"),
        ("block", "53047427"),
    ]
    y = 140
    for k, v in lines:
        d.text((80, y), k, font=font(26), fill=MUTED)
        d.text((330, y), v, font=font(26, mono=True), fill=FG)
        y += 46
    d.text((80, 525), "Frozen 6 Nov 2026 13:59 UTC, before any purchase. Ground truth: Base Sepolia public RPC.",
           font=font(24), fill=ACCENT)
    return im


def frame_compare():
    im, d = base()
    d.text((80, 45), "Same trap, two answers — t07 reverted-tx", font=font(40, bold=True), fill=FG)
    d.text((80, 100), "Same question  ·  Same price  ·  Different answers", font=font(26, bold=True), fill=ACCENT)
    # TxLens box
    d.rectangle([80, 155, 1200, 365], outline=RED, width=3)
    d.text((110, 180), "TxLens  (9002)", font=font(34, bold=True), fill=FG)
    d.text((110, 235), 'status: "not_found"  →  FAIL', font=font(30), fill=RED)
    d.text((110, 290), "cost $0.01  ·  receipt present  ·  signal recorded", font=font(24), fill=MUTED)
    # Truvian box — real t07 hashes from results-live/full-run-2026-11-06.json
    # (Truvian 8453, t07-reverted-tx): signal_hash
    # 0x1e082282cb1671801de841e906a8733d30aafb22cd003a093d1a3a573c60d285,
    # receipt_hash 0xb7f772e31a8722bb38410d391ddfd5a0348fedba1bc3a0b2cf841273451b3d95
    # (decoded from the receipt blob). Truncated: first 18 + last 6 chars.
    d.rectangle([80, 395, 1200, 600], outline=GREEN, width=3)
    d.text((110, 420), "Truvian  (8453)", font=font(34, bold=True), fill=FG)
    d.text((110, 475), 'status: "reverted"  ·  block / from / to all match  →  PASS', font=font(30), fill=GREEN)
    d.text((110, 530), "cost $0.01  ·  receipt present  ·  signal recorded", font=font(24), fill=MUTED)
    d.text((110, 562), "signal 0x1e082282cb167180…60d285  ·  receipt 0xb7f772e31a8722bb…1b3d95",
           font=font(19, mono=True), fill=FG)
    return im


def frame_fields():
    im, d = base()
    d.text((80, 50), "Scoring is strict — t07, field by field", font=font(40, bold=True), fill=FG)
    # t07 live rows (results-live/full-run-2026-11-06.json): TxLens 9002
    # answered status not_found with from/to/block_number ALL null — it
    # fails every scored field, not just status. Truvian 8453 passes all.
    rows = [
        ("field", "TxLens", "Truvian"),
        ("status", "✗ not_found", "✓ reverted"),
        ("from", "✗ —", "✓"),
        ("to", "✗ —", "✓"),
        ("block", "✗ —", "✓"),
        ("result", "FAIL", "PASS"),
    ]
    y = 140
    for i, (a, b, c) in enumerate(rows):
        fnt = font(30, bold=(i in (0, 5)))
        d.text((80, y), a, font=fnt, fill=FG if i else MUTED)
        bfill = RED if ("✗" in b or (i == 5 and b == "FAIL")) else FG
        cfill = GREEN if ("✓" in c or (i == 5 and c == "PASS")) else FG
        d.text((430, y), b, font=fnt, fill=bfill)
        d.text((800, y), c, font=fnt, fill=cfill)
        y += 52
    d.text((80, 480), "Truvian on confirmed txs: block, from, to, value all correct —",
           font=font(26), fill=FG)
    d.text((80, 520), "status blank → strict FAIL. A schema gap, not a wrong answer.",
           font=font(26), fill=ACCENT)
    return im


def frame_leaderboard():
    # v2: the ranked table is drawn from the CORRECTED re-score
    # (results-live/results-corrected-2026-11-08.json), not from a
    # screenshot of the strict leaderboard page. The v1 screenshot
    # (/tmp/leaderboard-full.png, ephemeral) no longer exists, and the
    # page renders IDs only, strict 3/12, and cost 0.0000 for unservable
    # providers. Drawing the table keeps names, corrected numbers, the
    # full "Ranked providers" heading and the disclosure note on screen,
    # with no cropped heading or cut-off row. Values:
    # Truvian 8453 4/12 (33%, $0.12, 12/12 receipts); TxLens 9002 2/12
    # (17%, $0.12, 12/12); LiveCert 4433 / Sigil 9010 / OnChain Intel 900
    # unservable, 0 served, $0 billed; $0.24 escrow credit in total.
    im, d = base()
    d.text((80, 45), "Live leaderboard — corrected re-score", font=font(38, bold=True), fill=FG)
    d.text((80, 105), "Ranked by pass rate, then traps run, then lower testnet cost.",
           font=font(26), fill=MUTED)
    d.text((80, 150), "Ranked providers", font=font(32, bold=True), fill=FG)
    cols = [("Rank", 80), ("Provider", 170), ("Pass rate", 520),
            ("Passed / run", 680), ("Billed", 940), ("Receipts", 1090)]
    y = 200
    for label, x in cols:
        d.text((x, y), label, font=font(26, bold=True), fill=MUTED)
    d.line([(80, 238), (1200, 238)], fill=(60, 80, 110), width=2)
    rows = [
        ("1", "Truvian 8453", "33%", "4 / 12", "$0.12", "12 / 12", GREEN),
        ("2", "TxLens 9002", "17%", "2 / 12", "$0.12", "12 / 12", FG),
        ("—", "LiveCert 4433", "—", "0 served (503)", "$0.00", "—", MUTED),
        ("—", "Sigil 9010", "—", "0 served (404)", "$0.00", "—", MUTED),
        ("—", "OnChain Intel 900", "—", "0 served (400)", "$0.00", "—", MUTED),
    ]
    y = 250
    for rank, prov, rate, passed, billed, receipts, rate_fill in rows:
        fnt = font(26)
        d.text((cols[0][1], y), rank, font=fnt, fill=FG)
        d.text((cols[1][1], y), prov, font=fnt, fill=FG)
        d.text((cols[2][1], y), rate, font=fnt, fill=rate_fill)
        d.text((cols[3][1], y), passed, font=fnt, fill=FG)
        d.text((cols[4][1], y), billed, font=fnt, fill=FG)
        d.text((cols[5][1], y), receipts, font=fnt, fill=FG)
        y += 46
    d.text((80, 490), "Corrected 8 Nov: Truvian 4/12 (strict original 3/12), t08 normalisation fix.",
           font=font(24), fill=ACCENT)
    d.text((80, 525), "Failed calls were not billed: $0.24 settled into Telegraph escrow credit.",
           font=font(24), fill=FG)
    d.text((80, 562), "Four versus two is two traps — evidence, not a verdict on provider quality.",
           font=font(26, bold=True), fill=ACCENT)
    return im


def frame_reproduce():
    im, d = base()
    d.text((80, 50), "Repeat it yourself", font=font(44, bold=True), fill=FG)
    d.text((80, 140), "$ python3 scripts/full_run.py     # 12 traps × providers",
           font=font(28, mono=True), fill=FG)
    d.text((80, 190), "$ python3 scripts/mini_run.py     # second-provider run",
           font=font(28, mono=True), fill=FG)
    d.text((80, 240), "See docs/how-to-run.md — frozen trap set, public ground truth,",
           font=font(26), fill=MUTED)
    d.text((80, 280), "receipts included. No wallet needed to check the evidence.",
           font=font(26), fill=MUTED)
    d.text((80, 420), "TrapTest — shows you the receipts.", font=font(40, bold=True), fill=ACCENT)
    d.text((80, 500), "Testnet evaluation only. No independent adoption is claimed.",
           font=font(26), fill=FG)
    return im


FRAMES = {"title": frame_title, "trap": frame_trap, "compare": frame_compare,
          "fields": frame_fields, "leaderboard": frame_leaderboard,
          "reproduce": frame_reproduce}


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("FAILED:", " ".join(cmd), "\n", r.stdout, r.stderr)
        sys.exit(1)
    return r


def ffprobe_dur(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "format=duration", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True)
    return float(r.stdout.strip())


def srt_time(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def main():
    # 1. Narration per shot (one clip per shot — natural pacing, no
    # per-sentence stitching).
    durs = []
    for shot in SHOTS:
        mp3 = HERE / f"{shot['key']}.mp3"
        if not mp3.exists():
            run(["/opt/hatch/bin/tts", "speak", "--text", shot["text"],
                 "--output", str(mp3)])
        durs.append(ffprobe_dur(mp3))
        print(shot["key"], f"{durs[-1]:.1f}s")

    # 2. Frames.
    frame_files = []
    for shot in SHOTS:
        png = HERE / f"{shot['key']}.png"
        FRAMES[shot["frame"]]().save(png)
        frame_files.append(png)

    # 3. SRT captions: sentences split proportionally by character count
    # within each shot (timings approximate — captions follow narration).
    import re
    def chunks(text):
        # Split into short caption chunks (<=60 chars) at sentence and
        # clause boundaries so captions stay to 1-2 lines.
        out = []
        for sent in re.split(r"(?<=[.!?])\s+", text):
            sent = sent.strip()
            if not sent:
                continue
            parts = re.split(r"(?<=[,—])\s+", sent)
            buf = ""
            for p in parts:
                if buf and len(buf) + 1 + len(p) > 60:
                    out.append(buf)
                    buf = p
                else:
                    buf = f"{buf} {p}".strip() if buf else p
            if buf:
                out.append(buf)
        return out
    srt = []
    t = 0.0
    idx = 1
    for shot, dur in zip(SHOTS, durs):
        caps = chunks(shot["text"])
        total = sum(len(s) for s in caps)
        cur = t
        for s in caps:
            span = dur * len(s) / total
            srt.append(f"{idx}\n{srt_time(cur)} --> {srt_time(cur + span)}\n{s}\n")
            idx += 1
            cur += span
        t += dur
    (HERE / "captions-v2.srt").write_text("\n".join(srt))
    total_dur = sum(durs)
    print(f"total narration: {total_dur:.1f}s")

    # 4. Assemble: still per shot for its audio duration (+0.4s pad),
    # concat, mux audio, burn captions.
    seg_files = []
    for shot, dur, png in zip(SHOTS, durs, frame_files):
        seg = HERE / f"{shot['key']}_seg.mp4"
        run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-i", str(png),
             "-i", str(HERE / f"{shot['key']}.mp3"),
             "-t", f"{dur + 0.4:.2f}", "-vf", "scale=1280:720,format=yuv420p",
             "-c:v", "libx264", "-r", "30", "-c:a", "aac", "-shortest", str(seg)])
        seg_files.append(seg)
    concat = HERE / "concat.txt"
    concat.write_text("".join(f"file '{s}'\n" for s in seg_files))
    out = HERE / "traptest-demo-2026-11-08.mp4"
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
         "-i", str(concat), "-c", "copy", str(HERE / "nocap.mp4")])
    # Burn captions (single re-encode).
    run(["ffmpeg", "-y", "-v", "error", "-i", str(HERE / "nocap.mp4"),
         "-vf", f"subtitles={HERE / 'captions-v2.srt'}:force_style='FontName=DejaVu Sans,FontSize=20,PrimaryColour=&HFFFFFF&,OutlineColour=&H000000&,BorderStyle=1,Outline=2,Alignment=2,MarginV=28'",
         "-c:a", "copy", str(out)])
    print("wrote", out, f"{ffprobe_dur(out):.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
