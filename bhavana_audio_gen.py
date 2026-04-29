#!/usr/bin/env python3
"""
Bhavana Practice Companion — Audio Generator (Chatterbox TTS)
==============================================================
Generates all guided meditation MP3s for the Bhavana Practice Companion.
Uses the same Chatterbox TTS pipeline as the BrahmaVihara app.

Usage:
    source /Users/gravisha/venvs/chatterbox/bin/activate
    python bhavana_audio_gen.py                # generate all missing
    python bhavana_audio_gen.py --dry-run      # preview, no generation
    python bhavana_audio_gen.py --force        # regenerate all
    python bhavana_audio_gen.py --phase settle # one phase only
    python bhavana_audio_gen.py --speed 0.80   # adjust speech pace

Phases: settle, sitting, walking_intro, walking, close
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
OUTPUT_DIR     = Path("audio")
SPEECH_SPEED   = 0.82   # meditative pace
LOUDNESS_TARGET = -18.0  # LUFS

# ─────────────────────────────────────────────────────────────
# SEGMENTS — all phrases for the Bhavana Practice Companion
# ─────────────────────────────────────────────────────────────
SEGMENTS = [

  # ── SETTLING (shared opening for all session types) ────────
  {"phase":"settle","index":1,  "filename":"settle_01.mp3","text":"Find a comfortable upright seat."},
  {"phase":"settle","index":2,  "filename":"settle_02.mp3","text":"Let the spine be naturally tall — not rigid, but gently lifted."},
  {"phase":"settle","index":3,  "filename":"settle_03.mp3","text":"Rest the hands gently in your lap."},
  {"phase":"settle","index":4,  "filename":"settle_04.mp3","text":"Close the eyes softly, or lower the gaze toward the floor."},
  {"phase":"settle","index":5,  "filename":"settle_05.mp3","text":"Take one slow, natural breath. Not controlling it — simply noticing."},
  {"phase":"settle","index":6,  "filename":"settle_06.mp3","text":"Take another breath. Feel the body soften slightly."},
  {"phase":"settle","index":7,  "filename":"settle_07.mp3","text":"And one more. Let the shoulders drop. Let the jaw release."},
  {"phase":"settle","index":8,  "filename":"settle_08.mp3","text":"You are arriving. There is nowhere else to be."},
  {"phase":"settle","index":9,  "filename":"settle_09.mp3","text":"Silently, set your intention for this practice."},
  {"phase":"settle","index":10, "filename":"settle_10.mp3","text":"May this sitting be of benefit — to myself and to all beings."},

  # ── SITTING ────────────────────────────────────────────────
  {"phase":"sitting","index":1,  "filename":"sitting_01.mp3","text":"Bring the attention to the breath."},
  {"phase":"sitting","index":2,  "filename":"sitting_02.mp3","text":"Not the idea of the breath — the actual, physical sensation."},
  {"phase":"sitting","index":3,  "filename":"sitting_03.mp3","text":"The coolness at the nostrils as you breathe in."},
  {"phase":"sitting","index":4,  "filename":"sitting_04.mp3","text":"The warmth as you breathe out."},
  {"phase":"sitting","index":5,  "filename":"sitting_05.mp3","text":"Or the gentle rise and fall of the abdomen."},
  {"phase":"sitting","index":6,  "filename":"sitting_06.mp3","text":"Choose one place, and rest the attention there."},
  {"phase":"sitting","index":7,  "filename":"sitting_07.mp3","text":"The mind will wander. This is its nature."},
  {"phase":"sitting","index":8,  "filename":"sitting_08.mp3","text":"When it does — and you notice — simply return."},
  {"phase":"sitting","index":9,  "filename":"sitting_09.mp3","text":"Without frustration. Without self-criticism."},
  {"phase":"sitting","index":10, "filename":"sitting_10.mp3","text":"Returning is the practice."},
  {"phase":"sitting","index":11, "filename":"sitting_11.mp3","text":"Breath by breath."},
  {"phase":"sitting","index":12, "filename":"sitting_12.mp3","text":"Moment by moment."},

  # ── WALKING INTRO ──────────────────────────────────────────
  {"phase":"walking_intro","index":1, "filename":"walking_intro_01.mp3","text":"Come to standing. Take a moment to feel the weight of the body."},
  {"phase":"walking_intro","index":2, "filename":"walking_intro_02.mp3","text":"Feel the contact of the feet with the ground."},
  {"phase":"walking_intro","index":3, "filename":"walking_intro_03.mp3","text":"The floor beneath you is solid. You are supported."},
  {"phase":"walking_intro","index":4, "filename":"walking_intro_04.mp3","text":"Walking meditation is not going somewhere — it is being somewhere."},
  {"phase":"walking_intro","index":5, "filename":"walking_intro_05.mp3","text":"Each step is complete in itself."},
  {"phase":"walking_intro","index":6, "filename":"walking_intro_06.mp3","text":"We will walk slowly. Much slower than normal."},
  {"phase":"walking_intro","index":7, "filename":"walking_intro_07.mp3","text":"With each step, be aware of lifting, moving, placing."},
  {"phase":"walking_intro","index":8, "filename":"walking_intro_08.mp3","text":"Lifting the foot... moving it forward... placing it down."},
  {"phase":"walking_intro","index":9, "filename":"walking_intro_09.mp3","text":"Let the practice begin."},

  # ── WALKING ────────────────────────────────────────────────
  {"phase":"walking","index":1, "filename":"walking_01.mp3","text":"Continue walking slowly."},
  {"phase":"walking","index":2, "filename":"walking_02.mp3","text":"Lifting... moving... placing."},
  {"phase":"walking","index":3, "filename":"walking_03.mp3","text":"When the mind wanders, gently bring it back to the feet."},
  {"phase":"walking","index":4, "filename":"walking_04.mp3","text":"Back to the feeling of the ground."},
  {"phase":"walking","index":5, "filename":"walking_05.mp3","text":"When you reach the end of your path, pause."},
  {"phase":"walking","index":6, "filename":"walking_06.mp3","text":"Stand for a moment. Feel the stillness."},
  {"phase":"walking","index":7, "filename":"walking_07.mp3","text":"Then turn slowly — and walk again."},
  {"phase":"walking","index":8, "filename":"walking_08.mp3","text":"The body knows how to do this."},
  {"phase":"walking","index":9, "filename":"walking_09.mp3","text":"Your task is simply to be present for it."},

  # ── CLOSING ────────────────────────────────────────────────
  {"phase":"close","index":1,  "filename":"close_01.mp3","text":"We close our practice with the Bhavana Society closing verse."},
  {"phase":"close","index":2,  "filename":"close_02.mp3","text":"May all beings be happy and secure."},
  {"phase":"close","index":3,  "filename":"close_03.mp3","text":"May all beings have happy minds."},
  {"phase":"close","index":4,  "filename":"close_04.mp3","text":"May all beings be free from suffering."},
  {"phase":"close","index":5,  "filename":"close_05.mp3","text":"May all beings quickly obtain liberation."},
  {"phase":"close","index":6,  "filename":"close_06.mp3","text":"Sit quietly for a moment. Notice the quality of the mind."},
  {"phase":"close","index":7,  "filename":"close_07.mp3","text":"Perhaps softer. Perhaps quieter."},
  {"phase":"close","index":8,  "filename":"close_08.mp3","text":"Whatever is here — it is the fruit of sincere effort."},
  {"phase":"close","index":9,  "filename":"close_09.mp3","text":"Take one slow breath."},
  {"phase":"close","index":10, "filename":"close_10.mp3","text":"And when you are ready, gently open the eyes."},
  {"phase":"close","index":11, "filename":"close_11.mp3","text":"Carry whatever stillness you have found here into the rest of your day."},
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
    parser = argparse.ArgumentParser(description="Generate Bhavana Practice Companion audio")
    parser.add_argument("--phase",   help="Only one phase: settle|sitting|walking_intro|walking|close")
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
            print(f"✗ Unknown phase '{args.phase}'. Valid: settle sitting walking_intro walking close")
            sys.exit(1)

    print(f"\nBhavana Practice Companion — Audio Generator")
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
        print(f"  ✓ Open index.html in a browser to test.")

if __name__ == "__main__":
    main()
