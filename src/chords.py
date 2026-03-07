import json
import re

class ChordLibrary:
    def __init__(self, file_path, subs_file_path=None):
        self.chord_data = self._load_json_data(file_path)
        self.substitutions = self._load_json_data(subs_file_path).get("substitutions", []) if subs_file_path else []
        
        self.note_to_midi = {
            'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4, 'F': 5,
            'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11
        }
        self.midi_to_note = {v: k for k, v in self.note_to_midi.items()}
        self.open_string_midi = {
            'E': 40, # Low E
            'A': 45,
            'D': 50,
            'G': 55,
            'B': 59,
            'e': 64  # High E
        }
        self.string_order = ['E', 'A', 'D', 'G', 'B', 'e']
        self.string_map = {
            5: 'E', 4: 'A', 3: 'D', 2: 'G', 1: 'B', 0: 'e'
        }

    def _load_json_data(self, file_path):
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: Chord library file not found at {file_path}")
            return {}
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from {file_path}")
            return {}
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return {}

    def _parse_chord_name(self, chord_name):
        original_chord_name = chord_name
        
        # 1. Extract the root note (e.g. C, C#, Bb). 
        # Match A-G, optionally followed by exactly one 'b' or '#'
        root_match = re.match(r'^([A-G][b#]?)(.*)', chord_name, re.IGNORECASE)
        if not root_match:
            return None, None
            
        root_note = root_match.group(1)
        # Normalize the root note (capitalize first letter, keep b/lowercase)
        if len(root_note) == 2:
            root_note = root_note[0].upper() + root_note[1].lower()
        else:
            root_note = root_note.upper()
            
        remaining_quality = root_match.group(2).strip().upper()

        # Map common quality abbreviations to full names from JSON
        quality_map = {
            '': 'Major',
            'M': 'Major',
            'MAJ': 'Major',
            '7': 'Dominant 7',
            'MAJ7': 'Major 7',
            'M7': 'Minor 7',
            '-7': 'Minor 7',
            'MIN7': 'Minor 7',
            '-': 'Minor',
            'MIN': 'Minor',
            'M7B5': 'Minor 7 Flat 5',
            '-7B5': 'Minor 7 Flat 5',
            'DIM7': 'Diminished 7',
            'O7': 'Diminished 7',
            'O': 'Diminished 7',
            '6': 'Major 6',
            'MIN6': 'Minor 6',
            '-6': 'Minor 6',
            'M6': 'Minor 6',
            'AUG7': 'Dominant 7', # Map to Dominant 7 for now
            '7ALTER#5': 'Dominant 7', # Specific case for F7 alter #5
        }
        
        # Clean up remaining quality string (remove spaces)
        clean_quality = remaining_quality.replace(' ', '')
        
        # Try direct match first
        standardized_quality = quality_map.get(clean_quality, None)
        if standardized_quality:
            return root_note, standardized_quality

        # Try to find a quality that is a substring of the remaining_quality
        for key, value in quality_map.items():
            if key and clean_quality.startswith(key):
                return root_note, value

        # Fallback for simple major if no quality is specified
        if not clean_quality:
            return root_note, 'Major'

        print(f"Warning: Could not determine quality for {original_chord_name}. Using Major.")
        return root_note, 'Major'

    def _get_fret_for_note_on_string(self, target_note, open_string_note):
        notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        target_note_index = notes.index(target_note)
        open_string_note_index = notes.index(open_string_note)
        fret = (target_note_index - open_string_note_index + 12) % 12
        return fret

    def _get_absolute_frets(self, root_note, selected_voicing):
        absolute_frets = [-1] * 6 # Initialize with muted strings
        
        # Determine the root string based on voicing name
        root_string_index = -1
        voicing_name = selected_voicing.get('name', '')
        if "E-string root" in voicing_name:
            root_string_index = 5  # Low E string
        elif "A-string root" in voicing_name:
            root_string_index = 4  # A string
        elif "D-string root" in voicing_name:
            root_string_index = 3  # D string
        
        # Calculate the absolute root fret on the chosen string
        actual_root_fret = 0
        if root_string_index != -1:
            open_string_note = self.string_map.get(root_string_index)
            if open_string_note:
                # Map notes like 'e' to 'E' for the note calculation
                open_string_obj_note = open_string_note.upper() if open_string_note == 'e' else open_string_note
                # Map note roots like 'Db' to 'C#' to match the notes array
                equivalents = {'Db': 'C#', 'Eb': 'D#', 'Gb': 'F#', 'Ab': 'G#', 'Bb': 'A#'}
                target_root = equivalents.get(root_note, root_note)
                actual_root_fret = self._get_fret_for_note_on_string(target_root, open_string_obj_note)

        for position in selected_voicing['positions']:
            string_name = self.string_map.get(position[0]) # Get string name from integer index
            if not string_name:
                print(f"Warning: Invalid string index {position[0]} in voicing for {root_note}")
                continue
            string_idx = self.string_order.index(string_name) # Get index in ordered_strings
            relative_fret = position[1]
            
            absolute_frets[string_idx] = relative_fret + actual_root_fret

        # Reorder frets to match ordered_strings (e, B, G, D, A, E)
        final_frets = [-1] * 6
        for i, s_name in enumerate(self.string_order):
            final_frets[i] = absolute_frets[i]

        return final_frets

    def get_chord_voicings(self, chord_name):
        root_note, quality = self._parse_chord_name(chord_name)
        if not root_note or not quality:
            print(f"Warning: Could not parse chord name: {chord_name}")
            return None

        # Apply substitutions
        for sub in self.substitutions:
            if quality == sub.get("original_quality"):
                print(f"Substitution applied: replaced {quality} with {sub.get('substituted_quality')} for {chord_name}")
                quality = sub.get("substituted_quality")
                
                # Apply root note offset if specified
                if "root_offset" in sub:
                     notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
                     # Normalize flats to sharps for lookup
                     equivalents = {'Db': 'C#', 'Eb': 'D#', 'Gb': 'F#', 'Ab': 'G#', 'Bb': 'A#'}
                     lookup_note = equivalents.get(root_note, root_note)
                     
                     if lookup_note in notes:
                         current_idx = notes.index(lookup_note)
                         new_idx = (current_idx + sub["root_offset"]) % 12
                         root_note = notes[new_idx]
                         print(f"  Root shifted by {sub['root_offset']} to {root_note}")
                break

        if quality not in self.chord_data:
            print(f"Warning: Chord quality '{quality}' not found in library for {chord_name}")
            return None

        voicings = self.chord_data[quality]
        if not voicings:
            print(f"Warning: No voicings found for quality '{quality}' in library.")
            return None

        valid_voicings = []
        for voicing in voicings:
            final_frets = self._get_absolute_frets(root_note, voicing)
            if final_frets is not None:
                valid_voicings.append({'frets': final_frets, 'name': voicing['name']})

        return valid_voicings if valid_voicings else None
