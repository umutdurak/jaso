# Future Feature Idea: Chord Melody Generator

This document outlines initial brainstorming for dynamically generating chord melody arrangements (where the melody note serves as the highest voice of the chord).

## The Core Challenge
Currently, Jaso treats melody optimization and chord voicing optimization as two separate pipelines. In a chord melody, the melody note *dictates* the chord voicing. The top note of the chord **must** be the melody note. This breaks the static JSON library approach because chords must be constructed dynamically based on the melody note's pitch and string position.

## Proposed Architecture

**1. A Dynamic "Drop-Voicing" Generator**
Instead of using a hardcoded JSON library of shapes, the engine would construct voicings on the fly using Drop 2, Drop 3, or Drop 2&4 voicings.
- **Identify:** Find the melody note (e.g., G4) and its current chord symbol (e.g., Cmaj7).
- **Analyze:** Determine the chord tones (C, E, G, B) and the melody note's role (G is the 5th).
- **Construct:** Stack the remaining notes *below* the melody note on adjacent lower strings.

**2. A Unified Cost Function (Aesthetics + Mechanics)**
The Viterbi algorithm handles the optimization, but the cost function becomes multidimensional:
- **Mechanical Cost:** Penalize large fret jumps and awkward stretches.
- **Harmonic Cost:** Penalize omitting guide tones (3rd or 7th).
- **Voice Leading Cost:** Reward smooth inner-voice movement between chords.

**3. Rhythmic Density Aesthetic Filter**
Playing a full chord on *every* melody note is clunky and often physically impossible at tempo. An aesthetic filter is needed:
- **Strong Beats:** Assign chords primarily to melody notes landing on strong beats (1 and 3).
- **Duration:** Prioritize chords on melody notes with longer durations (e.g., > quarter note).
- **Passing Notes:** For passing eighth notes, play only the single melody note, or perhaps add a single bass note.

## Required Engine Upgrades
1. **Music Theory Engine:** Teach Jaso to parse chord symbols into absolute pitches (using `music21.harmony`) to dynamically build shapes.
2. **Fretboard Geometry Engine:** Build a function that takes absolute pitches (e.g., `[C3, E3, B3, G4]`) and finds all physically playable fretting combinations.
3. **Unified Pipeline:** A new `--flavor chord_melody` flag that triggers a unified Viterbi pass, combining melody and chord events into a single timeline.
