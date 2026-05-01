# Everyday Mettā — Developer Documentation

## Overview

Everyday Mettā is a voice-responsive web app for short loving-kindness (mettā)
practices woven into daily life. It is a single HTML file with an `audio/`
directory of pre-generated MP3s and falls back to the browser's Web Speech API
when MP3s are unavailable.

It is the third app in the Bhavana Society suite, following BrahmaVihara and
the Bhavana Practice Companion.

**Live:** https://gravishankar.github.io/BhavanaSociety/Everyday-metta/everyday-metta-bhavana.html
**Repo branch:** `everyday-metta` (merged to `main`)

---

## File Structure

```
Everyday-metta/
├── everyday-metta-bhavana.html      App — all UI, logic, and content
├── everyday_metta_audio_gen.py      Chatterbox TTS batch generator
├── everyday-metta-voice-script.txt  Original phrase list (source of truth for text)
├── readme.txt                       Quick-start for non-developers
└── audio/                           152 generated MP3 files
    ├── prompt_*.mp3                 4  UI navigation phrases
    ├── confirm_*.mp3                8  Activity confirmation phrases
    ├── eating_*.mp3                 17 Eating practice phrases
    ├── coffee_tea_*.mp3             16 Coffee/Tea practice phrases
    ├── cooking_*.mp3                18 Cooking practice phrases
    ├── traffic_*.mp3                18 Traffic/Commute practice phrases
    ├── waiting_*.mp3                17 Waiting in Line practice phrases
    ├── walking_*.mp3                18 Walking practice phrases
    ├── cleaning_*.mp3               18 Cleaning practice phrases
    └── starting_work_*.mp3          18 Starting Work practice phrases
```

---

## Architecture

### Tech Stack

- **Frontend:** Vanilla HTML/CSS/JavaScript — no build tools, no frameworks
- **Voice input:** Web Speech Recognition API (Chrome/Safari)
- **Voice output:** Pre-generated Chatterbox TTS MP3s, fallback to Web Speech Synthesis API
- **Deployment:** GitHub Pages (static, no server required)

### State Machine

The app moves through six states:

```
idle → ask_activity → confirm_activity → ask_duration → guiding → closing
```

| State | What happens |
|---|---|
| `idle` | Splash and home screen |
| `ask_activity` | Speaks "What are you doing?", listens for speech |
| `confirm_activity` | Low-confidence match — asks user to confirm |
| `ask_duration` | Speaks "Short practice or two minutes?", listens |
| `guiding` | Plays phrases in sequence with post-phrase silence |
| `closing` | Practice complete, offers another/repeat/finish |

### Audio Engine

`speakText(seg)` accepts either a `{text, filename, pause}` object or a plain string.

1. If `mp3Available` is true and a `filename` is present, plays `audio/<filename>` via `HTMLAudioElement`.
2. After audio ends, waits `pause` seconds (the meditative silence between phrases).
3. Falls back to Web Speech Synthesis if the MP3 errors or autoplay is blocked.

```javascript
// Example segment object
{text:"May they be safe.", filename:"eating_short_04.mp3", pause:7}
```

Pause values are tuned per phrase — shorter for narrative phrases (~5s),
longer for wish phrases (~7-9s).

### Activity Recognition

`parseActivity(transcript)` scans the transcript against each activity's
`synonyms` array. It scores matches by synonym specificity (longer synonym =
higher confidence) and returns `{id, label, confidence}`.

If `confidence < 0.9` the app asks the user to confirm before proceeding.

### Voice Controls (during practice)

Recognised intents during playback:

| Spoken | Intent |
|---|---|
| "pause", "hold on" | pause |
| "resume", "continue" | resume |
| "repeat", "again" | repeat current phrase |
| "stop", "finish" | end practice |
| "short", "quick" | choose short duration |
| "longer", "two minutes" | choose long duration |
| "yes", "correct", "yeah" | confirm activity |
| "no", "wrong", "nope" | reject activity |

---

## Audio Generation

### Generator Script

`everyday_metta_audio_gen.py` uses the same Chatterbox TTS pipeline as
BrahmaVihara and the Bhavana Practice Companion.

**Setup (one-time):**
```bash
source /Users/gravisha/venvs/chatterbox/bin/activate
```

**Generate all 152 files:**
```bash
python everyday_metta_audio_gen.py
```

**Options:**
```bash
python everyday_metta_audio_gen.py --dry-run          # preview, no generation
python everyday_metta_audio_gen.py --force            # overwrite existing files
python everyday_metta_audio_gen.py --phase eating     # one activity only
python everyday_metta_audio_gen.py --speed 0.75       # slower pace
```

**Valid phase names:**
`prompt`, `confirm`, `eating`, `coffee_tea`, `cooking`, `traffic`,
`waiting`, `walking`, `cleaning`, `starting_work`

### Audio Processing Pipeline

For each phrase:

1. Chatterbox TTS generates a `.wav` at 24 kHz on Apple Silicon MPS
2. ffmpeg processes it in one pass:
   - `atempo=0.82` — slows to meditative pace
   - `loudnorm=I=-18` — normalises loudness to -18 LUFS
   - Converts to MP3 at quality 2 (~192 kbps)
3. Temporary `.wav` is deleted

### Audio Settings

| Setting | Value | Notes |
|---|---|---|
| Speech speed | 0.82x | Matches BrahmaVihara and Bhavana Companion |
| Loudness | -18 LUFS | Comfortable listening level |
| Format | MP3, ~192 kbps | Browser-compatible |
| Post-phrase pause | 5–9 seconds | Set per phrase in HTML, not in audio file |
| Total files | 152 | ~5 MB total |

### File Naming Convention

```
{activity}_{duration}_{index:02d}.mp3

Examples:
  eating_short_01.mp3
  coffee_tea_long_05.mp3
  starting_work_short_03.mp3
  prompt_what_are_you_doing.mp3
  confirm_cooking.mp3
```

---

## Content Structure

### Phrases per Activity

| Activity | Short | Long | Total |
|---|---|---|---|
| Eating | 6 | 11 | 17 |
| Coffee or Tea | 6 | 10 | 16 |
| Cooking | 6 | 12 | 18 |
| Traffic/Commute | 6 | 12 | 18 |
| Waiting in Line | 6 | 11 | 17 |
| Walking | 6 | 12 | 18 |
| Cleaning | 6 | 12 | 18 |
| Starting Work | 6 | 12 | 18 |
| System prompts | — | — | 4 |
| Confirmations | — | — | 8 |
| **Total** | | | **152** |

### Practice Scripts

Each activity has:
- **Short** (~30 seconds): 6 phrases — pause, observe context, 3-4 mettā wishes
- **Long** (~2 minutes): 10-12 phrases — pause, broader context, expanded wishes,
  closing wish for self

---

## Design System

Tokens match the Bhavana Society design system used across all three apps:

```css
--bg:       #0D1410   /* Near-black green */
--metta:    #4CAF80   /* Mettā green */
--karuna:   #E07070   /* Karuṇā red */
--mudita:   #E0B040   /* Muditā gold */
--upekkha:  #6090E0   /* Upekkhā blue */
--gold:     #C8A84B
```

Activity-specific orb colours:

| Activity | Colour |
|---|---|
| Eating | Mettā green |
| Coffee or Tea | Warm amber |
| Cooking | Karuṇā red |
| Traffic | Upekkhā blue |
| Waiting | Muditā gold |
| Walking | Mettā green |
| Cleaning | Soft teal |
| Starting Work | Soft purple |

---

## Deployment

Hosted on GitHub Pages from the `main` branch of
`https://github.com/gravishankar/BhavanaSociety`.

Pages is configured to serve from root `/` on `main`. The app is accessible at:

```
https://gravishankar.github.io/BhavanaSociety/Everyday-metta/everyday-metta-bhavana.html
```

### To deploy changes:

```bash
cd /Users/gravisha/projects/BhavanaSociety/bhavana-app-mvp
# make changes, then:
git add Everyday-metta/
git commit -m "your message"
git push origin main
```

GitHub Pages rebuilds automatically within ~2 minutes.

---

## Browser Compatibility

| Browser | Voice Input | MP3 Audio |
|---|---|---|
| Chrome (desktop) | ✅ | ✅ |
| Safari (iOS/macOS) | ✅ | ✅ |
| Firefox | ❌ No SpeechRecognition | ✅ (browse mode) |
| Edge | ✅ | ✅ |

On browsers without SpeechRecognition, the app falls back to a tap-to-choose
activity grid. On browsers without MP3 autoplay, it falls back to Web Speech
Synthesis.

---

## Related Apps

| App | Description | Segments |
|---|---|---|
| BrahmaVihara | Four divine abodes guided meditation | 169 MP3s, ~21 min |
| Bhavana Practice Companion | Sitting and walking meditation | ~90 MP3s |
| Everyday Mettā | Voice-guided daily activity practices | 152 MP3s |

All three use the same:
- Chatterbox TTS pipeline (`0.82x` speed, `-18 LUFS`)
- Bhavana Society design tokens
- MP3-first audio engine with Web Speech fallback

---

## Virtual Environment

```
/Users/gravisha/venvs/chatterbox
Python 3.11 (Apple Silicon ARM64)
Packages: torch, torchaudio, chatterbox-tts, ffmpeg (Homebrew)
```

Activate:
```bash
source /Users/gravisha/venvs/chatterbox/bin/activate
```

The Chatterbox model is downloaded once from Hugging Face (~500 MB) and cached
locally. Subsequent runs use the local cache.

---

*Last updated: April 30, 2026*
*Status: Complete — 152 audio files generated, deployed to GitHub Pages*
