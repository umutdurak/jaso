# Jaso (Jazz Songs)

Jaso is a Python-based command-line tool designed to assist musicians in creating guitar tablature for jazz standards. It takes a MusicXML music notation file as input, analyzes its melody and chord progression, and then generates optimized guitar tablature for both the melody and the chords, prioritizing ease of playing.

## Features

-   **Score Parsing:** Reads and extracts musical information (melody notes, chord symbols, lyrics, and rehearsal marks) from **MusicXML** (`.musicxml`, `.xml`, `.mxl`) and **LilyPond** (`.ly`) files.
-   **Chord Library Integration:** Utilizes a comprehensive JSON-based library of guitar chord voicings with style-specific "flavors" (Classical, Freddie Green, Gypsy Jazz).
-   **Dual-Staff Tablature:** Generates a professional "Dual-Staff" layout, separating the **Accompaniment (Chords)** and the **Lead (Melody)** into two vertically aligned rhythmic grids.
-   **MusicXML Export:** Exports the optimized arrangement back into a MusicXML file (`.musicxml`) with full `<technical>` tablature annotations, ready for native playback and rendering in MuseScore 4.
-   **Smart Optimization:** Employs a Viterbi dynamic programming algorithm to find the absolute easiest sequence of both chord voicings and melody fingerings, minimizing fretboard hand movement.
-   **Instrument Decoupling:** Supports any stringed instrument (e.g., Ukulele, Banjo, or custom tunings) via external JSON instrument definitions.
-   **Extensible Configuration:** All layout parameters (CPQN, measures per line), musical defaults, and optimization weights are externalized to JSON.
-   **Rhythmic Alignment:** Features a fixed rhythmic grid with explicit measure bars (`|`), section markers (`[A]`), and synchronized lyrics.

## Configuration

Jaso is designed to be highly configurable without modifying the source code:

-   **[app_config.json](app_config.json):** Controls layout settings (`beats_per_measure`, `measures_per_line`, `global_cpqn`) and optimizer cost weights (`melody_fret_weight`, `melody_string_weight`).
-   **[instrument_guitar_standard.json](instrument_guitar_standard.json):** Defines the instrument's open string MIDI values, string display order, and chromatic scale normalization.
-   **[quality_config.json](quality_config.json):** Centralizes base chord abbreviations and fallback logic.

## Development Process

This entire repository and its codebase were developed exclusively with **vibe coding**. Initially, the project was built using GeminiCLI, but it is now developed using Antigravity with Gemini 3.1. Every line of code, every file, and every command executed was generated and guided by the AI in an interactive command-line environment.

## Getting Started

### Prerequisites

-   Python 3.x
-   Git (for cloning the repository)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone git@github.com:umutdurak/jaso.git
    cd jaso
    ```
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### Usage

To generate tablature, run the `main.py` script with your MusicXML or LilyPond file, choose your chord flavor, and specify your desired output text file. You can also optionally export the optimized score back to MusicXML for MuseScore:

```bash
python3 main.py <path_to_score_file> <output_tablature_file.txt> --flavor <classical|freddie|gypsy> [--xml <output_musicxml_file>]
```

**Example:**

```bash
python3 main.py songs/misty.mxl output_misty.txt --flavor freddie --xml output_misty_optimized.musicxml
```

This will generate `output_misty.txt` with the text tablature using Freddie Green chord voicings, and also export `output_misty_optimized.musicxml` which can be opened in MuseScore to view and play the synchronized tablature.

*Note: For backward compatibility, you can still pass an explicit chords `.json` file in place of the `--flavor` and output file sequence.*

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.
