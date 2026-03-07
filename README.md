# Jaso (Jazz Songs)

Jaso is a Python-based command-line tool designed to assist musicians in creating guitar tablature for jazz standards. It takes a MusicXML music notation file as input, analyzes its melody and chord progression, and then generates optimized guitar tablature for both the melody and the chords, prioritizing ease of playing.

## Features

-   **MusicXML Parsing:** Reads and extracts musical information (melody notes, chord symbols) from MusicXML (`.musicxml`, `.xml`, `.mxl`) files.
-   **Chord Library Integration:** Utilizes a comprehensive JSON-based library of guitar chord voicings.
-   **Optimal Chord Progression:** Employs a dynamic programming algorithm to select the most "easy-to-play" sequence of chord voicings based on minimizing fret-hand movement.
-   **Tablature Generation:** Outputs a basic text-based tablature for the melody and the optimized chord progression.

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

To generate tablature, run the `main.py` script with your MusicXML file, choose your chord flavor, and specify your desired output file:

```bash
python3 main.py --flavor <classical|freddie|gypsy> <path_to_your_musicxml_file.musicxml> <output_tablature_file.txt>
```

**Example:**

```bash
python3 main.py --flavor gypsy sample.musicxml output.txt
```

This will generate `output.txt` in the current directory with the tablature using the Gypsy Jazz playing style simplifications and voicings.

*Note: For backward compatibility, you can still pass an explicit chords `.json` file in place of the `--flavor` and output file sequence.*

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.
