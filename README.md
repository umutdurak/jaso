# Jaso (Jazz Songs)

Jaso is a Python-based command-line tool designed to assist musicians in creating guitar tablature for jazz standards. It takes a LilyPond music notation file as input, analyzes its melody and chord progression, and then generates optimized guitar tablature for both the melody and the chords, prioritizing ease of playing.

## Features

-   **LilyPond Parsing:** Reads and extracts musical information (melody notes, chord symbols) from LilyPond (`.ly`) files.
-   **Chord Library Integration:** Utilizes a comprehensive JSON-based library of guitar chord voicings.
-   **Optimal Chord Progression:** Employs a dynamic programming algorithm to select the most "easy-to-play" sequence of chord voicings based on minimizing fret-hand movement.
-   **Tablature Generation:** Outputs a basic text-based tablature for the melody and the optimized chord progression.

## Development Process

This entire repository and its codebase were developed exclusively with **wibe coding using Gemini**. Every line of code, every file, and every command executed was generated and guided by the Gemini AI model in an interactive command-line environment.

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
    *Note: While `music21` is a dependency, the current LilyPond parsing relies on a regex-based approach due to external LilyPond executable issues. Future versions might re-integrate `music21`'s full capabilities if the LilyPond environment is stable.*

### Usage

To generate tablature, run the `main.py` script with your LilyPond file, chord library, and desired output file:

```bash
python3 main.py <path_to_your_lilypond_file.ly> <path_to_your_chords_json_file.json> <output_tablature_file.txt>
```

**Example:**

```bash
python3 main.py sample.ly chords.json output.txt
```

This will generate `output.txt` in the current directory with the tablature.

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.
