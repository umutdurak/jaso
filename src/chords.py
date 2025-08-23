"""
Loads and manages chord shape data from a JSON file.
"""
import json

def load_chord_library(file_path):
    """
    Loads the chord voicings from the specified JSON file.

    :param file_path: The absolute path to the chords.json file.
    :return: A dictionary containing the chord library, or None on error.
    """
    try:
        with open(file_path, 'r') as f:
            chord_library = json.load(f)
        print(f"Successfully loaded chord library from {file_path}")
        return chord_library
    except FileNotFoundError:
        print(f"Error: Chord library file not found at {file_path}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {file_path}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None