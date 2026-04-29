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

  # ── DISTRACTION RESPONSES ──────────────────────────────────
  # thoughts
  {"phase":"distraction","index":1,  "filename":"distraction_thoughts_1.mp3","text":"The mind wandered — and now it has returned. This is exactly the practice. Without the wandering, there is nothing to return from. Gently, without scolding, bring the attention back to the breath. The breath is always here, always patient."},
  {"phase":"distraction","index":2,  "filename":"distraction_thoughts_2.mp3","text":"Thoughts are like clouds moving through the sky — the sky does not chase them. You are the sky. Let the thought be seen, noted simply as thinking, and release it. Return to the breath."},
  {"phase":"distraction","index":3,  "filename":"distraction_thoughts_3.mp3","text":"Notice that you noticed. That noticing is awareness itself — pure, clear, unconditioned. From that awareness, let the breath be the anchor. One breath at a time. This moment. This breath."},
  # discomfort
  {"phase":"distraction","index":4,  "filename":"distraction_discomfort_1.mp3","text":"Before moving, bring a gentle curiosity to the sensation. Where is it exactly? What is its quality — sharp, dull, spreading, throbbing? Does it change as you observe it? Often the direct attention of mindfulness itself is enough to soften discomfort. If it is calling for a postural adjustment, move slowly and deliberately — without losing awareness."},
  {"phase":"distraction","index":5,  "filename":"distraction_discomfort_2.mp3","text":"The body holds tension we carry unconsciously. Meet this discomfort as a teacher. Breathe into the area with kindness. If it is simply the protest of an unused muscle, let equanimity hold it — knowing it will pass. If it is genuine pain, attend to the body with the same compassion you would offer a dear friend."},
  {"phase":"distraction","index":6,  "filename":"distraction_discomfort_3.mp3","text":"Offer the discomfort the quality of compassion. The body is impermanent, these sensations are impermanent. You need not fight them, nor be ruled by them. Simply observe, with a steady and open attention, what is here."},
  # drowsy
  {"phase":"distraction","index":7,  "filename":"distraction_drowsy_1.mp3","text":"Drowsiness is one of the five hindrances — and like all of them, it responds to being seen clearly. Open the eyes slightly. Lift the gaze. Sit up a little taller and take a few slightly fuller breaths. You are brightening the quality of attention — not forcing, but kindling."},
  {"phase":"distraction","index":8,  "filename":"distraction_drowsy_2.mp3","text":"When the dullness is heavy, the walking practice is a gift. Even a few minutes of slow, deliberate walking can wake the mind and bring it into the present moment far more readily than sitting with heavy eyes. Consider transitioning to walking, then returning to the sitting."},
  {"phase":"distraction","index":9,  "filename":"distraction_drowsy_3.mp3","text":"Bring energy to the practice. Not straining, but a gentle determination. Notice the texture of the drowsiness itself — is it heavy, foggy, warm? Curiosity itself is the antidote to dullness."},
  # restless
  {"phase":"distraction","index":10, "filename":"distraction_restless_1.mp3","text":"Do not fight the restlessness — that is like trying to flatten water with your hands. Instead, let it be the object of meditation. Where does it live in the body? Is it in the chest? The jaw? The hands? Name it quietly: restlessness, restlessness. The act of observing loosens its hold."},
  {"phase":"distraction","index":11, "filename":"distraction_restless_2.mp3","text":"Restlessness often carries urgency — the feeling that something must be done right now. This urgency is also just a mental event. Let the breath become the anchor: long, slow, deliberate breaths. Let each exhale be a small release. You do not need to act on this urgency. It will pass."},
  {"phase":"distraction","index":12, "filename":"distraction_restless_3.mp3","text":"Recall why you sat down. Not to achieve anything, not to be somewhere else — but to cultivate the steadiness of mind that makes everything else possible. Restlessness, I see you. Now return. Breath by breath."},
  # doubt
  {"phase":"distraction","index":13, "filename":"distraction_doubt_1.mp3","text":"Doubt is the fifth hindrance — and it often arrives dressed as wisdom. Is this working? Am I doing it right? Does this even matter? Notice that this too is just a thought arising in the mind. You do not need to answer these questions right now. Return to what is directly known: the breath, the body, this moment."},
  {"phase":"distraction","index":14, "filename":"distraction_doubt_2.mp3","text":"Trust what you have already tasted from this practice — even the small moments of stillness, of returning, of noticing. Those are real. Doubt cannot take them away. Continue, humbly and without fanfare. The clarity comes not by forcing but by continuing."},
  {"phase":"distraction","index":15, "filename":"distraction_doubt_3.mp3","text":"The proof of the practice is not in the session, but in the quality of the life you lead between sessions. You are building something slowly. The doubt you feel is the resistance before the ground gives way. Simply sit. Simply practice."},
  # emotion
  {"phase":"distraction","index":16, "filename":"distraction_emotion_1.mp3","text":"When strong emotions arise in meditation, they are not obstacles — they are the practice itself. You are being shown what needs to be seen. Do not push the emotion away, and do not be swept into its story. Simply stay with the feeling as a physical sensation: where is it in the body? What is its quality? Breathe with it. Let it be seen."},
  {"phase":"distraction","index":17, "filename":"distraction_emotion_2.mp3","text":"Meet this emotion with loving-friendliness extended first to yourself. You are a human being, and you are feeling what human beings feel. This is not weakness. Whisper inwardly: may I hold this with gentleness. May I hold this with courage. May I find relief and ease. Then return, slowly, to the breath."},
  {"phase":"distraction","index":18, "filename":"distraction_emotion_3.mp3","text":"The heart must be soft enough to feel and strong enough to hold what it feels. Allow the emotion its space — without elaborating the story around it, and without suppressing it. Just this feeling. Just this breath. Just this moment. You are safe here."},
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
    parser.add_argument("--phase",   help="Only one phase: settle|sitting|walking_intro|walking|close|distraction")
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
