# Parses LilyPond files to extract melody and chords using regular expressions.

import re

def parse_lilypond_file(file_path):
    
    # Parses a LilyPond file using regular expressions to extract notes and chords.
    # This is a simplified parser that looks for specific variable assignments.

    # :param file_path: The absolute path to the .ly file.
    # :return: A tuple containing two lists: (melody_events, chord_events).
    
    melody_events = []
    chord_events = []
    try:
        with open(file_path, 'r') as f:
            content = f.read()

        # Regex to find a variable assignment like melody = \relative c\' { ... }
        melody_search = re.search(r"melody\s*=\s*\\relative[^{]*{\s*([^}]*?)\s*}", content, re.DOTALL)
        if melody_search:
            melody_content = melody_search.group(1).strip()
            # Simple split by whitespace to get individual notes/commands
            melody_events = re.split(r'\s+', melody_content)

        # Regex to find a chordmode block like mychords = \chordmode { ... }
        chords_search = re.search(r"mychords\s*=\s*\\chordmode\s*{\s*([^}]*?)\s*}", content, re.DOTALL)
        if chords_search:
            chords_content = chords_search.group(1).strip()
            # Simple split by whitespace to get individual chords
            chord_events = re.split(r'\s+', chords_content)

        if not melody_events and not chord_events:
            print("Warning: Could not find melody or chord blocks in the file.")

        return melody_events, chord_events

    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return None, None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None, None
