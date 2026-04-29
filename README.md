# Bhāvanā Practice Companion

A mobile-first meditation timer for sitting and walking practice in the Bhavana Society tradition. Runs entirely in the browser — no server, no account, no tracking.

## What it does

- **Sitting meditation** — 20-minute guided session with breath awareness instruction, then silence
- **Walking meditation** — 20-minute guided session with lifting/moving/placing instruction
- **Sitting + Walking** — 30-minute combined practice (Bhavana Society style)
- **Tibetan bowl tones** — synthesized bowl sound at the start of each phase and at the close
- **Guided voice** — real MP3 recordings play first; Web Speech API is used as a fallback
- **Distraction support** — "Mind wandering?" button pauses the timer and offers gentle, Bhavana-rooted guidance for six common obstacles, read aloud
- **Journal** — daily reflection prompts and a practice streak tracker
- **Guidance screen** — working with the five hindrances and common distractions

## How to use

Open `index.html` (or `bhavana-practice-companion.html`) in any modern browser. No build step, no dependencies.

For the MP3 audio to work, the `audio/` folder must be in the same directory as the HTML file. The app falls back gracefully to Web Speech if an MP3 is missing or blocked by the browser.

## Audio files

All audio files live in `audio/`. The app uses:

| File | Used for |
|------|----------|
| `sitting_intro_01–06.mp3` | Sitting practice guided intro |
| `walking_intro_01–06.mp3` | Walking practice guided intro |
| `closing_01.mp3` | Closing verse |
| `reminder_breath_01.mp3` | Breath reminder (available, not currently scheduled) |
| `reminder_walk_01.mp3` | Walk reminder (available, not currently scheduled) |
| `reminder_body_01.mp3` | Body reminder (available, not currently scheduled) |

## Offline / PWA

A `sw.js` service worker and `manifest.webmanifest` are included. When served over HTTPS the app can be installed to the home screen and used offline.

## Related

**BrahmaVihara app** — `/BrahmaVihara/brahma-vihara-meditation-app.html` — a companion app for the four Brahma Viharas (Metta, Karuna, Mudita, Upekkha). Same design system.

## Tradition

This app follows the Bhavana Society tradition as taught by Bhante Gunaratana at the Bhavana Society, High View, West Virginia. It is offered freely, without fee or registration.
