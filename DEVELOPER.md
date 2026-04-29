# Developer Notes — Bhāvanā Practice Companion

## Architecture

Single-file app: `bhavana-practice-companion.html`. All CSS and JavaScript are inline. No build tools, no npm, no framework. The only external dependency is the Google Fonts stylesheet (loaded via `<link>`; the app works without it, just with system fonts).

`index.html` is a redirect shim that forwards to `bhavana-practice-companion.html`.

## Design system

Matches the BrahmaVihara app (`/BrahmaVihara/brahma-vihara-meditation-app.html`) exactly. Shared conventions:

- **Palette** — dark green base (`--bg: #0D1410`). Each session type has its own accent color:
  - Sitting → `--sage: #6BAD8A`
  - Walking → `--amber: #C8943C`
  - Sitting+Walking / closing → `--clay: #B06060`
  - Equanimity/slate tones → `--slate: #7090B0`
- **Typography** — `Playfair Display` (headings, phrases, italic labels), `Lato` (body, UI)
- **Radius tokens** — `--r: 12px`, `--r-lg: 20px`
- **Ambient orbs** — three `position:fixed` blurred circles, animated with `amb-drift`

## Key data structures

### `PHASES` object
Each phase is keyed by id (`settle`, `sitting`, `walking_intro`, `walking`, `close`). Fields:

```js
{
  id:      string,   // key
  label:   string,   // displayed in player
  color:   string,   // hex accent
  dark:    string,   // darker accent for orb gradient
  rgb:     string,   // "r,g,b" for rgba() use
  sym:     string,   // symbol shown on orb
  bg:      string,   // player background dark color
  action:  string,   // breath guide top line
  sub:     string,   // breath guide sub line
  mins:    number,   // phase duration
  phrase:  string,   // initial phrase shown in player
  guided:  Array<{text, pause, filename?}>  // voice script
}
```

Each `guided` segment has:
- `text` — shown on screen and used as Web Speech fallback
- `pause` — silence in seconds *after* the spoken text ends
- `filename` — optional MP3 filename in `audio/`; if absent, falls back to Web Speech

### `SESSIONS` object
Maps session mode to an ordered array of phase ids:

```js
SESSIONS = {
  sitting: ['settle', 'sitting', 'close'],
  walking: ['settle', 'walking_intro', 'walking', 'close'],
  combo:   ['settle', 'sitting', 'walking_intro', 'walking', 'close']
}
```

### `DISTRACTION` object
Six distraction types: `thoughts`, `discomfort`, `drowsy`, `restless`, `doubt`, `emotion`. Each has:

```js
{
  borderColor: string,       // CSS color for response card accent
  attr:        string,       // attribution line
  responses:   string[]      // 3 rotating text responses
}
```

Responses rotate via `distractionCount[type]` — each time a type is selected, the next response in the array is shown (wraps around). This means a practitioner who hits the same type repeatedly gets varied guidance.

## Audio engine

Priority order:
1. **MP3** — `playSegment()` tries `new Audio(AUDIO_PATH + filename)` first
2. **Web Speech** — `speakFallback()` fires on `error` or `NotAllowedError`

`AUDIO_PATH` defaults to `'./audio/'`. Change this constant to point elsewhere.

Voice preferences for Web Speech (in order): `Daniel`, `Moira`, `Google UK English Male`, `Arthur`, `Alex`, `Samantha`, `Karen`, then any English voice, then whatever is available.

Distraction responses use a separate `speakDistractionResponse()` function (no MP3 involved) with a slightly slower rate (`0.62`) and softer pitch (`0.78`) than the guided script to feel gentler and more contemplative.

Bowl tones are synthesized via Web Audio — two slightly detuned sine oscillators with an exponential gain envelope. Frequencies per phase:

| Phase | Frequency |
|-------|-----------|
| settle | 440 Hz |
| sitting | 432 Hz |
| walking_intro | 396 Hz |
| walking | 396 Hz |
| close | 440 Hz |
| End bell | 396 Hz |

## Player state

Global variables (intentionally simple, no framework):

| Variable | Purpose |
|---|---|
| `playerPhaseIds` | Ordered array of phase ids for current session |
| `curPhaseIdx` | Index into `playerPhaseIds` |
| `timerSecs` | Seconds remaining in current phase |
| `timerTotal` | Total seconds for current phase (for ring progress) |
| `timerRunning` | Boolean; guards all audio and timer callbacks |
| `timerIv` | `setInterval` handle for the countdown |
| `breathId` | `setTimeout` handle for breath cycle |
| `guidedTimeout` | `setTimeout` handle for guided script sequencing |
| `speakTimeout` | `setTimeout` handle for initial bowl→voice delay |

`stopTimers()` clears all of these and calls `stopSpeech()`.

## Distraction panel

The panel (`#distraction-panel`) is `position:fixed` at z-index 600 (above the player at 500). It:

1. Clears `timerIv` and `breathId` (pauses countdown without setting `timerRunning = false`)
2. Calls `stopSpeech()` to silence any in-progress guidance
3. On "Return to Practice", restores the interval and breath cycle

The timer does not lose elapsed time during the panel — `timerSecs` is not reset.

## Adding new content

### New phase
1. Add an entry to `PHASES` with all required fields
2. Add a `guided[]` array of segments (use `filename` only if an MP3 exists)
3. Add the phase id to the relevant `SESSIONS` arrays

### New distraction type
1. Add an entry to `DISTRACTION` with `borderColor`, `attr`, and 3 `responses`
2. Add a `.dp-opt` button in `#dp-options` with `onclick="selectDistraction('yourKey')"`

### New session type
1. Add to `SESSIONS` with an ordered array of existing phase ids
2. Add a session card in the Home screen HTML
3. Add a label entry in `openPlayer()`

## PWA / offline

`sw.js` and `manifest.webmanifest` handle installation and offline caching. Icons are in `icons/`. To update the cache version, edit the cache name string in `sw.js`.

## Browser compatibility

Tested in: Chrome, Safari (iOS + macOS), Firefox. Web Audio and Web Speech are both required for full functionality. The app works without them (no audio), but that is a degraded experience. Safari on iOS requires a user gesture before any AudioContext or speech can start — the play button in the player satisfies this requirement.
