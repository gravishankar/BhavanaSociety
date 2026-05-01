Everyday Metta — Bhavana Society
=================================

Purpose
-------
A voice-responsive web app that guides short metta (loving-kindness)
practices during everyday activities: eating, coffee or tea, cooking,
commuting, waiting in line, walking, cleaning, and starting work.

The user speaks what they are doing. The app recognises the activity,
asks for a short (~30 second) or longer (~2 minute) practice, then
plays the guided meditation with Chatterbox TTS audio and appropriate
silence between phrases.

Live URL
--------
https://gravishankar.github.io/BhavanaSociety/Everyday-metta/everyday-metta-bhavana.html

Branch
------
everyday-metta (merged to main for deployment)

What is in this folder
----------------------
  everyday-metta-bhavana.html     Main app — open in a browser to use
  everyday_metta_audio_gen.py     Generates all 152 MP3 audio files
  everyday-metta-voice-script.txt Original voice script (phrase text + filenames)
  audio/                          152 generated Chatterbox TTS MP3 files

Eight activities
----------------
  Eating              eating_short_*.mp3 / eating_long_*.mp3
  Coffee or Tea       coffee_tea_short_*.mp3 / coffee_tea_long_*.mp3
  Cooking             cooking_short_*.mp3 / cooking_long_*.mp3
  Traffic/Commute     traffic_short_*.mp3 / traffic_long_*.mp3
  Waiting in Line     waiting_short_*.mp3 / waiting_long_*.mp3
  Walking             walking_short_*.mp3 / walking_long_*.mp3
  Cleaning            cleaning_short_*.mp3 / cleaning_long_*.mp3
  Starting Work       starting_work_short_*.mp3 / starting_work_long_*.mp3

Audio files: 152 total
  4   system prompt phrases
  8   activity confirmation phrases
  68  practice phrases (8 activities x 2 durations, 6-12 phrases each)
  72  (short + long across all activities)

How to use the app
------------------
1. Open everyday-metta-bhavana.html in Chrome or Safari
2. Tap "Begin Practice"
3. Tap "Start voice practice" or choose an activity card
4. Say what you are doing (e.g. "eating", "making coffee", "driving")
5. Say "short" or "longer" when asked
6. Listen — the Chatterbox voice guides you through metta phrases
7. Say "pause", "repeat", or "stop" at any point

How to regenerate audio
-----------------------
If you want to regenerate the MP3 files:

  source /Users/gravisha/venvs/chatterbox/bin/activate
  cd /path/to/Everyday-metta
  python everyday_metta_audio_gen.py --dry-run    # preview
  python everyday_metta_audio_gen.py              # generate all
  python everyday_metta_audio_gen.py --force      # overwrite existing
  python everyday_metta_audio_gen.py --phase eating  # one activity only

Audio settings
--------------
  Speech speed    0.82x (meditative pace, matches BrahmaVihara and Bhavana apps)
  Loudness        -18 LUFS
  Format          MP3, ~192 kbps
  Post-phrase pause  5-9 seconds per phrase (embedded in app, not in audio file)

Virtual environment
-------------------
  /Users/gravisha/venvs/chatterbox
  Python 3.11, Apple Silicon MPS acceleration

Developer documentation
-----------------------
See DEVELOPER.md in this folder.

Related apps
------------
  BrahmaVihara/   Four divine abodes guided meditation (169 segments, ~21 min)
  bhavana-app-mvp/ Sitting and walking meditation practice companion
