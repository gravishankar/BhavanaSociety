#!/usr/bin/env python3
"""
Everyday Mettā — Audio Generator (Chatterbox TTS)
==================================================
Generates all 121 guided meditation MP3s for the Everyday Mettā app.
Follows the same pipeline as BrahmaVihara and Bhavana Practice Companion.

Usage:
    source /Users/gravisha/venvs/chatterbox/bin/activate
    python everyday_metta_audio_gen.py                # generate all missing
    python everyday_metta_audio_gen.py --dry-run      # preview, no generation
    python everyday_metta_audio_gen.py --force        # regenerate all
    python everyday_metta_audio_gen.py --phase eating # one phase only
    python everyday_metta_audio_gen.py --speed 0.82   # adjust speech pace

Phases: prompt, confirm, eating, coffee_tea, cooking, traffic,
        waiting, walking, cleaning, starting_work
Output: audio/ directory (next to this script)
"""

import os
import sys
import time
import argparse
import subprocess
from pathlib import Path

# ─────────────────────────────────────────────────────────────
# MONKEYPATCH: Fix Chatterbox watermarker issue
# ─────────────────────────────────────────────────────────────
def patch_chatterbox():
    try:
        import perth
        if perth.PerthImplicitWatermarker is None:
            perth.PerthImplicitWatermarker = perth.DummyWatermarker
            print("  ✓ Watermarker patched")
    except Exception as e:
        print(f"  ⚠ Could not patch watermarker: {e}")

patch_chatterbox()

try:
    import torchaudio as ta
    import torch
    from chatterbox.tts import ChatterboxTTS
except ImportError as e:
    print(f"✗ Import error: {e}")
    print("  Activate venv: source /Users/gravisha/venvs/chatterbox/bin/activate")
    sys.exit(1)

# ─────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────
OUTPUT_DIR      = Path("audio")
SPEECH_SPEED    = 0.82   # meditative pace — matches BrahmaVihara/Bhavana apps
LOUDNESS_TARGET = -18.0  # LUFS

# ─────────────────────────────────────────────────────────────
# SEGMENTS — 121 phrases for Everyday Mettā
# ─────────────────────────────────────────────────────────────
SEGMENTS = [

  # ── SYSTEM PROMPTS (UI navigation) ────────────────────────
  {"phase":"prompt","index":1,  "filename":"prompt_what_are_you_doing.mp3",  "text":"What are you doing right now?"},
  {"phase":"prompt","index":2,  "filename":"prompt_short_or_long.mp3",       "text":"Short practice, or two minutes?"},
  {"phase":"prompt","index":3,  "filename":"prompt_end_choice.mp3",          "text":"Another one, reflect, or finish?"},
  {"phase":"prompt","index":4,  "filename":"prompt_didnt_catch.mp3",         "text":"I didn't catch that. Say eating, tea, cooking, traffic, waiting, walking, cleaning, or starting work."},

  # ── CONFIRMATION PROMPTS (low-confidence matches) ──────────
  {"phase":"confirm","index":1, "filename":"confirm_eating.mp3",             "text":"I heard eating. Is that right?"},
  {"phase":"confirm","index":2, "filename":"confirm_coffee_tea.mp3",         "text":"I heard tea or coffee. Is that right?"},
  {"phase":"confirm","index":3, "filename":"confirm_cooking.mp3",            "text":"I heard cooking. Is that right?"},
  {"phase":"confirm","index":4, "filename":"confirm_traffic.mp3",            "text":"I heard traffic or commuting. Is that right?"},
  {"phase":"confirm","index":5, "filename":"confirm_waiting.mp3",            "text":"I heard waiting. Is that right?"},
  {"phase":"confirm","index":6, "filename":"confirm_walking.mp3",            "text":"I heard walking. Is that right?"},
  {"phase":"confirm","index":7, "filename":"confirm_cleaning.mp3",           "text":"I heard cleaning. Is that right?"},
  {"phase":"confirm","index":8, "filename":"confirm_starting_work.mp3",      "text":"I heard starting work. Is that right?"},

  # ── EATING — Short (~30 seconds) ──────────────────────────
  {"phase":"eating","index":1,  "filename":"eating_short_01.mp3","text":"Before the first bite, pause."},
  {"phase":"eating","index":2,  "filename":"eating_short_02.mp3","text":"This food traveled far to reach you."},
  {"phase":"eating","index":3,  "filename":"eating_short_03.mp3","text":"Many hands planted, picked, packed, and prepared it."},
  {"phase":"eating","index":4,  "filename":"eating_short_04.mp3","text":"May they be safe."},
  {"phase":"eating","index":5,  "filename":"eating_short_05.mp3","text":"May they be nourished."},
  {"phase":"eating","index":6,  "filename":"eating_short_06.mp3","text":"May they live with ease."},

  # ── EATING — Long (~2 minutes) ────────────────────────────
  {"phase":"eating","index":7,  "filename":"eating_long_01.mp3","text":"Before eating, pause for a moment."},
  {"phase":"eating","index":8,  "filename":"eating_long_02.mp3","text":"This meal did not begin in your kitchen."},
  {"phase":"eating","index":9,  "filename":"eating_long_03.mp3","text":"It began in soil, in sun, in rain, in effort."},
  {"phase":"eating","index":10, "filename":"eating_long_04.mp3","text":"Farmers rose early. Workers loaded trucks in the dark."},
  {"phase":"eating","index":11, "filename":"eating_long_05.mp3","text":"Someone stocked the shelves. Someone cooked with care."},
  {"phase":"eating","index":12, "filename":"eating_long_06.mp3","text":"Hold all of them gently in your mind."},
  {"phase":"eating","index":13, "filename":"eating_long_07.mp3","text":"May they be safe."},
  {"phase":"eating","index":14, "filename":"eating_long_08.mp3","text":"May they be healthy."},
  {"phase":"eating","index":15, "filename":"eating_long_09.mp3","text":"May they be peaceful."},
  {"phase":"eating","index":16, "filename":"eating_long_10.mp3","text":"May they live with ease."},
  {"phase":"eating","index":17, "filename":"eating_long_11.mp3","text":"Eat with gratitude."},

  # ── COFFEE / TEA — Short (~30 seconds) ───────────────────
  {"phase":"coffee_tea","index":1,  "filename":"coffee_tea_short_01.mp3","text":"Before the first sip, pause."},
  {"phase":"coffee_tea","index":2,  "filename":"coffee_tea_short_02.mp3","text":"This comfort reached you through many hands."},
  {"phase":"coffee_tea","index":3,  "filename":"coffee_tea_short_03.mp3","text":"Remember the farmers, pickers, drivers, and sellers."},
  {"phase":"coffee_tea","index":4,  "filename":"coffee_tea_short_04.mp3","text":"May they be safe."},
  {"phase":"coffee_tea","index":5,  "filename":"coffee_tea_short_05.mp3","text":"May they be healthy."},
  {"phase":"coffee_tea","index":6,  "filename":"coffee_tea_short_06.mp3","text":"May they live with ease."},

  # ── COFFEE / TEA — Long (~2 minutes) ─────────────────────
  {"phase":"coffee_tea","index":7,  "filename":"coffee_tea_long_01.mp3","text":"Before the first sip, pause."},
  {"phase":"coffee_tea","index":8,  "filename":"coffee_tea_long_02.mp3","text":"This drink did not begin here."},
  {"phase":"coffee_tea","index":9,  "filename":"coffee_tea_long_03.mp3","text":"Many people worked in heat, rain, effort, and distance."},
  {"phase":"coffee_tea","index":10, "filename":"coffee_tea_long_04.mp3","text":"This warmth has come to you through their labor."},
  {"phase":"coffee_tea","index":11, "filename":"coffee_tea_long_05.mp3","text":"Remember the farmers, harvesters, drivers, roasters, and sellers."},
  {"phase":"coffee_tea","index":12, "filename":"coffee_tea_long_06.mp3","text":"May they be safe."},
  {"phase":"coffee_tea","index":13, "filename":"coffee_tea_long_07.mp3","text":"May they be healthy."},
  {"phase":"coffee_tea","index":14, "filename":"coffee_tea_long_08.mp3","text":"May they be peaceful."},
  {"phase":"coffee_tea","index":15, "filename":"coffee_tea_long_09.mp3","text":"May their lives unfold with ease."},
  {"phase":"coffee_tea","index":16, "filename":"coffee_tea_long_10.mp3","text":"Drink with gratitude."},

  # ── COOKING — Short (~30 seconds) ────────────────────────
  {"phase":"cooking","index":1,  "filename":"cooking_short_01.mp3","text":"As you cook, pause."},
  {"phase":"cooking","index":2,  "filename":"cooking_short_02.mp3","text":"These hands are acts of care."},
  {"phase":"cooking","index":3,  "filename":"cooking_short_03.mp3","text":"Someone will receive this nourishment."},
  {"phase":"cooking","index":4,  "filename":"cooking_short_04.mp3","text":"May they be well."},
  {"phase":"cooking","index":5,  "filename":"cooking_short_05.mp3","text":"May this food bring them ease."},
  {"phase":"cooking","index":6,  "filename":"cooking_short_06.mp3","text":"May you be at peace as you prepare it."},

  # ── COOKING — Long (~2 minutes) ──────────────────────────
  {"phase":"cooking","index":7,  "filename":"cooking_long_01.mp3","text":"As your hands move through this work, pause."},
  {"phase":"cooking","index":8,  "filename":"cooking_long_02.mp3","text":"Cooking is one of the oldest forms of love."},
  {"phase":"cooking","index":9,  "filename":"cooking_long_03.mp3","text":"You are turning simple ingredients into nourishment."},
  {"phase":"cooking","index":10, "filename":"cooking_long_04.mp3","text":"Think of those who will eat what you prepare."},
  {"phase":"cooking","index":11, "filename":"cooking_long_05.mp3","text":"And those who cannot cook tonight."},
  {"phase":"cooking","index":12, "filename":"cooking_long_06.mp3","text":"And those who go without."},
  {"phase":"cooking","index":13, "filename":"cooking_long_07.mp3","text":"May all beings be nourished."},
  {"phase":"cooking","index":14, "filename":"cooking_long_08.mp3","text":"May you find ease in this work."},
  {"phase":"cooking","index":15, "filename":"cooking_long_09.mp3","text":"May those who eat feel cared for."},
  {"phase":"cooking","index":16, "filename":"cooking_long_10.mp3","text":"May they be well."},
  {"phase":"cooking","index":17, "filename":"cooking_long_11.mp3","text":"May they be at peace."},
  {"phase":"cooking","index":18, "filename":"cooking_long_12.mp3","text":"May they live with ease."},

  # ── TRAFFIC / COMMUTE — Short (~30 seconds) ──────────────
  {"phase":"traffic","index":1,  "filename":"traffic_short_01.mp3","text":"At this moment, pause."},
  {"phase":"traffic","index":2,  "filename":"traffic_short_02.mp3","text":"Everyone around you wants to get somewhere safe."},
  {"phase":"traffic","index":3,  "filename":"traffic_short_03.mp3","text":"Everyone is carrying something."},
  {"phase":"traffic","index":4,  "filename":"traffic_short_04.mp3","text":"May these travelers be safe."},
  {"phase":"traffic","index":5,  "filename":"traffic_short_05.mp3","text":"May they reach where they need to go in peace."},
  {"phase":"traffic","index":6,  "filename":"traffic_short_06.mp3","text":"May you arrive with ease."},

  # ── TRAFFIC / COMMUTE — Long (~2 minutes) ────────────────
  {"phase":"traffic","index":7,  "filename":"traffic_long_01.mp3","text":"In this delay, pause."},
  {"phase":"traffic","index":8,  "filename":"traffic_long_02.mp3","text":"Every car around you holds a life."},
  {"phase":"traffic","index":9,  "filename":"traffic_long_03.mp3","text":"Someone is late and worried."},
  {"phase":"traffic","index":10, "filename":"traffic_long_04.mp3","text":"Someone is tired."},
  {"phase":"traffic","index":11, "filename":"traffic_long_05.mp3","text":"Someone is on the way to something they love."},
  {"phase":"traffic","index":12, "filename":"traffic_long_06.mp3","text":"Someone is driving toward a hard day."},
  {"phase":"traffic","index":13, "filename":"traffic_long_07.mp3","text":"We are all trying to move through this world."},
  {"phase":"traffic","index":14, "filename":"traffic_long_08.mp3","text":"May all these travelers be safe."},
  {"phase":"traffic","index":15, "filename":"traffic_long_09.mp3","text":"May they be free from stress."},
  {"phase":"traffic","index":16, "filename":"traffic_long_10.mp3","text":"May they be peaceful."},
  {"phase":"traffic","index":17, "filename":"traffic_long_11.mp3","text":"May they reach where they need to go with ease."},
  {"phase":"traffic","index":18, "filename":"traffic_long_12.mp3","text":"May you too arrive safely and at peace."},

  # ── WAITING IN LINE — Short (~30 seconds) ────────────────
  {"phase":"waiting","index":1,  "filename":"waiting_short_01.mp3","text":"This pause is unexpected."},
  {"phase":"waiting","index":2,  "filename":"waiting_short_02.mp3","text":"Let it be a practice."},
  {"phase":"waiting","index":3,  "filename":"waiting_short_03.mp3","text":"Everyone here is waiting too."},
  {"phase":"waiting","index":4,  "filename":"waiting_short_04.mp3","text":"May they be patient and at ease."},
  {"phase":"waiting","index":5,  "filename":"waiting_short_05.mp3","text":"May you be patient and at ease."},
  {"phase":"waiting","index":6,  "filename":"waiting_short_06.mp3","text":"May this moment soften."},

  # ── WAITING IN LINE — Long (~2 minutes) ──────────────────
  {"phase":"waiting","index":7,  "filename":"waiting_long_01.mp3","text":"You did not plan for this wait."},
  {"phase":"waiting","index":8,  "filename":"waiting_long_02.mp3","text":"And yet here it is."},
  {"phase":"waiting","index":9,  "filename":"waiting_long_03.mp3","text":"Look around at the others waiting."},
  {"phase":"waiting","index":10, "filename":"waiting_long_04.mp3","text":"Each of them has somewhere to be."},
  {"phase":"waiting","index":11, "filename":"waiting_long_05.mp3","text":"Each has things weighing on them today."},
  {"phase":"waiting","index":12, "filename":"waiting_long_06.mp3","text":"We are briefly sharing this small inconvenience."},
  {"phase":"waiting","index":13, "filename":"waiting_long_07.mp3","text":"May each person here be well."},
  {"phase":"waiting","index":14, "filename":"waiting_long_08.mp3","text":"May they feel a little lighter."},
  {"phase":"waiting","index":15, "filename":"waiting_long_09.mp3","text":"May impatience soften into presence."},
  {"phase":"waiting","index":16, "filename":"waiting_long_10.mp3","text":"May you and everyone here be at peace."},
  {"phase":"waiting","index":17, "filename":"waiting_long_11.mp3","text":"May this moment be enough."},

  # ── WALKING — Short (~30 seconds) ────────────────────────
  {"phase":"walking","index":1,  "filename":"walking_short_01.mp3","text":"With each step, a quiet wish."},
  {"phase":"walking","index":2,  "filename":"walking_short_02.mp3","text":"Notice the people you pass."},
  {"phase":"walking","index":3,  "filename":"walking_short_03.mp3","text":"Each one wants to be happy and free from harm."},
  {"phase":"walking","index":4,  "filename":"walking_short_04.mp3","text":"May they be safe."},
  {"phase":"walking","index":5,  "filename":"walking_short_05.mp3","text":"May they be well."},
  {"phase":"walking","index":6,  "filename":"walking_short_06.mp3","text":"May they move through today with ease."},

  # ── WALKING — Long (~2 minutes) ──────────────────────────
  {"phase":"walking","index":7,  "filename":"walking_long_01.mp3","text":"As your feet meet the ground, pause inwardly."},
  {"phase":"walking","index":8,  "filename":"walking_long_02.mp3","text":"You are moving through a world full of lives."},
  {"phase":"walking","index":9,  "filename":"walking_long_03.mp3","text":"The person ahead of you has worries and joys."},
  {"phase":"walking","index":10, "filename":"walking_long_04.mp3","text":"The person behind you does too."},
  {"phase":"walking","index":11, "filename":"walking_long_05.mp3","text":"With each step, extend a quiet wish."},
  {"phase":"walking","index":12, "filename":"walking_long_06.mp3","text":"May the people I pass be safe."},
  {"phase":"walking","index":13, "filename":"walking_long_07.mp3","text":"May they be healthy and strong."},
  {"phase":"walking","index":14, "filename":"walking_long_08.mp3","text":"May they know peace today."},
  {"phase":"walking","index":15, "filename":"walking_long_09.mp3","text":"May they find ease in ordinary moments."},
  {"phase":"walking","index":16, "filename":"walking_long_10.mp3","text":"May you too feel the ground beneath you."},
  {"phase":"walking","index":17, "filename":"walking_long_11.mp3","text":"May you walk with care and without fear."},
  {"phase":"walking","index":18, "filename":"walking_long_12.mp3","text":"May this journey hold something good."},

  # ── CLEANING — Short (~30 seconds) ───────────────────────
  {"phase":"cleaning","index":1,  "filename":"cleaning_short_01.mp3","text":"As you clean, pause."},
  {"phase":"cleaning","index":2,  "filename":"cleaning_short_02.mp3","text":"This work is an act of care."},
  {"phase":"cleaning","index":3,  "filename":"cleaning_short_03.mp3","text":"Others will move through this space."},
  {"phase":"cleaning","index":4,  "filename":"cleaning_short_04.mp3","text":"May they feel ease here."},
  {"phase":"cleaning","index":5,  "filename":"cleaning_short_05.mp3","text":"May this home be a place of peace."},
  {"phase":"cleaning","index":6,  "filename":"cleaning_short_06.mp3","text":"May all who enter be well."},

  # ── CLEANING — Long (~2 minutes) ─────────────────────────
  {"phase":"cleaning","index":7,  "filename":"cleaning_long_01.mp3","text":"Cleaning is quiet, unglamorous care."},
  {"phase":"cleaning","index":8,  "filename":"cleaning_long_02.mp3","text":"And yet it matters."},
  {"phase":"cleaning","index":9,  "filename":"cleaning_long_03.mp3","text":"As your hands work, let the mind open."},
  {"phase":"cleaning","index":10, "filename":"cleaning_long_04.mp3","text":"Think of those who will use this space."},
  {"phase":"cleaning","index":11, "filename":"cleaning_long_05.mp3","text":"Think of those who clean spaces they will never inhabit."},
  {"phase":"cleaning","index":12, "filename":"cleaning_long_06.mp3","text":"Workers who clean offices, hospitals, and homes unseen."},
  {"phase":"cleaning","index":13, "filename":"cleaning_long_07.mp3","text":"May they be respected."},
  {"phase":"cleaning","index":14, "filename":"cleaning_long_08.mp3","text":"May their labor be honored."},
  {"phase":"cleaning","index":15, "filename":"cleaning_long_09.mp3","text":"May this space hold peace for all who enter it."},
  {"phase":"cleaning","index":16, "filename":"cleaning_long_10.mp3","text":"May those who rest here feel ease."},
  {"phase":"cleaning","index":17, "filename":"cleaning_long_11.mp3","text":"May your own effort today be enough."},
  {"phase":"cleaning","index":18, "filename":"cleaning_long_12.mp3","text":"May you find satisfaction in this care."},

  # ── STARTING WORK — Short (~30 seconds) ──────────────────
  {"phase":"starting_work","index":1,  "filename":"starting_work_short_01.mp3","text":"Before the first task, pause."},
  {"phase":"starting_work","index":2,  "filename":"starting_work_short_02.mp3","text":"Set a quiet intention."},
  {"phase":"starting_work","index":3,  "filename":"starting_work_short_03.mp3","text":"May my work today cause no harm."},
  {"phase":"starting_work","index":4,  "filename":"starting_work_short_04.mp3","text":"May it bring some good."},
  {"phase":"starting_work","index":5,  "filename":"starting_work_short_05.mp3","text":"May I meet others with patience."},
  {"phase":"starting_work","index":6,  "filename":"starting_work_short_06.mp3","text":"May this day unfold with ease."},

  # ── STARTING WORK — Long (~2 minutes) ────────────────────
  {"phase":"starting_work","index":7,  "filename":"starting_work_long_01.mp3","text":"Before you open the first message, pause."},
  {"phase":"starting_work","index":8,  "filename":"starting_work_long_02.mp3","text":"You are about to enter a day of effort and attention."},
  {"phase":"starting_work","index":9,  "filename":"starting_work_long_03.mp3","text":"There will be small frustrations."},
  {"phase":"starting_work","index":10, "filename":"starting_work_long_04.mp3","text":"There will be moments of connection."},
  {"phase":"starting_work","index":11, "filename":"starting_work_long_05.mp3","text":"You will affect others through your words and actions today."},
  {"phase":"starting_work","index":12, "filename":"starting_work_long_06.mp3","text":"Set a quiet intention now."},
  {"phase":"starting_work","index":13, "filename":"starting_work_long_07.mp3","text":"May my work cause no harm."},
  {"phase":"starting_work","index":14, "filename":"starting_work_long_08.mp3","text":"May it offer something of value."},
  {"phase":"starting_work","index":15, "filename":"starting_work_long_09.mp3","text":"May I listen more than I react."},
  {"phase":"starting_work","index":16, "filename":"starting_work_long_10.mp3","text":"May I meet difficulty with patience."},
  {"phase":"starting_work","index":17, "filename":"starting_work_long_11.mp3","text":"May those I work with be well."},
  {"phase":"starting_work","index":18, "filename":"starting_work_long_12.mp3","text":"May this day, in some small way, be good."},
]

# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────
def get_device():
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"

def process_audio_ffmpeg(wav_path, mp3_path, speed):
    try:
        cmd = [
            "ffmpeg", "-i", str(wav_path),
            "-filter:a", f"atempo={speed},loudnorm=I={LOUDNESS_TARGET}",
            "-codec:a", "libmp3lame",
            "-qscale:a", "2",
            "-y", str(mp3_path)
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        wav_path.unlink(missing_ok=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"    ✗ ffmpeg error: {e.stderr.decode() if e.stderr else e}")
        return False
    except Exception as e:
        print(f"    ✗ Process error: {e}")
        return False

def generate_audio(model, segment, output_path, speed):
    try:
        wav = model.generate(segment["text"])
        temp_wav = output_path.parent / f"{output_path.stem}_temp.wav"
        ta.save(str(temp_wav), wav, model.sr)
        return process_audio_ffmpeg(temp_wav, output_path, speed)
    except Exception as e:
        print(f"    ✗ ERROR {output_path.name}: {e}")
        return False

# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Generate Everyday Mettā audio")
    parser.add_argument("--phase",   help="Only one phase: prompt|confirm|eating|coffee_tea|cooking|traffic|waiting|walking|cleaning|starting_work")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force",   action="store_true")
    parser.add_argument("--speed",   type=float, default=0.82)
    args = parser.parse_args()

    global SPEECH_SPEED
    SPEECH_SPEED = args.speed

    segments = SEGMENTS
    if args.phase:
        segments = [s for s in SEGMENTS if s["phase"] == args.phase]
        if not segments:
            valid = "prompt confirm eating coffee_tea cooking traffic waiting walking cleaning starting_work"
            print(f"✗ Unknown phase '{args.phase}'. Valid: {valid}")
            sys.exit(1)

    print(f"\nEveryday Mettā — Audio Generator")
    print(f"{'─'*55}")
    print(f"  Segments : {len(segments)}")
    print(f"  Speed    : {SPEECH_SPEED}x")
    print(f"  Output   : {OUTPUT_DIR}/")
    if args.dry_run: print(f"  Mode     : DRY RUN")
    if args.force:   print(f"  Mode     : FORCE regenerate")
    print()

    if args.dry_run:
        for i, seg in enumerate(segments, 1):
            status = "EXISTS" if (OUTPUT_DIR / seg["filename"]).exists() else "NEW"
            print(f"  [{i:03d}/{len(segments)}] [{status:6s}] {seg['filename']}  \"{seg['text'][:50]}\"")
        return

    device = get_device()
    print(f"Loading Chatterbox model on {device}...")
    try:
        model = ChatterboxTTS.from_pretrained(device=device)
        print(f"✓ Model loaded (sample rate: {model.sr} Hz)\n")
    except Exception as e:
        print(f"✗ Failed to load model: {e}")
        sys.exit(1)

    OUTPUT_DIR.mkdir(exist_ok=True)
    generated = skipped = errors = 0
    start = time.time()

    for i, seg in enumerate(segments, 1):
        out = OUTPUT_DIR / seg["filename"]
        if out.exists() and not args.force:
            print(f"  [{i:03d}/{len(segments)}] ⟳ skip  {seg['filename']}")
            skipped += 1
            continue
        print(f"  [{i:03d}/{len(segments)}] ▶ gen   {seg['filename']}  \"{seg['text'][:45]}\"")
        ok = generate_audio(model, seg, out, SPEECH_SPEED)
        if ok: generated += 1
        else:  errors += 1

    elapsed = time.time() - start
    print(f"\n{'─'*55}")
    print(f"  Generated : {generated}")
    print(f"  Skipped   : {skipped}  (already existed)")
    print(f"  Errors    : {errors}")
    print(f"  Time      : {elapsed:.1f}s")
    if errors == 0 and generated > 0:
        print(f"\n  ✓ Done. Audio files ready in audio/")
        print(f"  ✓ Open everyday-metta-bhavana.html in a browser to test.")

if __name__ == "__main__":
    main()
