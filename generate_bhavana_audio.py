#!/usr/bin/env python3
"""
Generate Bhavana MVP meditation audio segments with local Chatterbox TTS.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path


def patch_chatterbox():
    try:
        import perth  # type: ignore
        if perth.PerthImplicitWatermarker is None:
            perth.PerthImplicitWatermarker = perth.DummyWatermarker
    except Exception:
        pass


patch_chatterbox()

try:
    import torch
    import torchaudio as ta
    from chatterbox.tts import ChatterboxTTS
except Exception as exc:
    print(f"Import failed: {exc}")
    print("Activate /Users/gravisha/venvs/chatterbox first.")
    sys.exit(1)


ROOT = Path(__file__).parent
AUDIO_DIR = ROOT / "audio"
SCRIPTS_PATH = ROOT / "audio_scripts.json"
LOUDNESS_TARGET = -18.0


def process_to_mp3(temp_wav: Path, out_mp3: Path, speed: float) -> bool:
    cmd = [
        "ffmpeg", "-i", str(temp_wav),
        "-filter:a", f"atempo={speed},loudnorm=I={LOUDNESS_TARGET}",
        "-codec:a", "libmp3lame", "-qscale:a", "2",
        "-y", str(out_mp3)
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        temp_wav.unlink(missing_ok=True)
        return True
    except subprocess.CalledProcessError as exc:
        print(f"ffmpeg failed for {out_mp3.name}: {exc}")
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--speed", type=float, default=0.82)
    parser.add_argument("--device", choices=["auto", "cpu", "mps"], default="auto")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.device == "cpu":
        device = "cpu"
    elif args.device == "mps":
        device = "mps"
    else:
        device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"Loading Chatterbox on {device}...")
    model = ChatterboxTTS.from_pretrained(device=device)

    AUDIO_DIR.mkdir(exist_ok=True)
    scripts = json.loads(SCRIPTS_PATH.read_text())

    total = 0
    generated = 0
    for group in scripts.values():
        for seg in group:
            total += 1
            out_mp3 = AUDIO_DIR / seg["filename"]
            if out_mp3.exists() and not args.force:
                print(f"skip {out_mp3.name}")
                continue
            print(f"gen  {out_mp3.name}")
            if args.dry_run:
                continue
            wav = model.generate(seg["text"])
            temp_wav = AUDIO_DIR / f"{out_mp3.stem}_temp.wav"
            ta.save(str(temp_wav), wav, model.sr)
            if process_to_mp3(temp_wav, out_mp3, args.speed):
                generated += 1

    print(f"Done. total={total} generated={generated}")


if __name__ == "__main__":
    main()
