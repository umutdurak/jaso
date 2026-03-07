import json
import re

class ChordLibrary:
    def __init__(self, file_path, subs_file_path=None):
        self.chord_data = self._load_json_data(file_path)
        
        # Load quality configuration
        base_config = self._load_json_data("quality_config.json")
        self.aliases = base_config.get("aliases", {})
        self.fallbacks = base_config.get("fallbacks", {})
        
        # Load substitutions and style-specific settings
        subs_data = self._load_json_data(subs_file_path) if subs_file_path else {}
        self.substitutions = subs_data.get("substitutions", [])
        
        # Merge style-specific aliases and fallbacks
        if "aliases" in subs_data:
            self.aliases.update(subs_data["aliases"])
        if "fallbacks" in subs_data:
            self.fallbacks.update(subs_data["fallbacks"])
            
        # Load instrument configuration (default to guitar)
        instrument_config = self._load_json_data("instrument_guitar_standard.json")
        self.open_string_midi = instrument_config.get("open_string_midi", {})
        self.string_order = instrument_config.get("string_order", [])
        self.notes = instrument_config.get("notes", [])
        self.enharmonics = instrument_config.get("enharmonic_equivalents", {})
        
        # Derived mappings
        self.note_to_midi = {note: i % 12 for i, note in enumerate(self.notes)}
        self.string_map = {len(self.string_order)-1-i: s for i, s in enumerate(self.string_order)}

    def _load_json_data(self, file_path):
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Silent fail for substitutions as they are optional, but log for library
            if "quality_config" not in file_path and "substitutions" not in file_path:
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
        
        # 1. Extract the root note (e.g. C, C#, Bb, B-). 
        # Match A-G, optionally followed by 'b', '#', or '-' (for flat)
        root_match = re.match(r'^([A-G][b#\-]?)(.*)', chord_name, re.IGNORECASE)
        if not root_match:
            return None, None
            
        root_note = root_match.group(1)
        # Normalize root: replace '-' with 'b' for flat, handle capitalization
        root_note = root_note.replace('-', 'b')
        if len(root_note) == 2:
            root_note = root_note[0].upper() + root_note[1].lower()
        else:
            root_note = root_note.upper()
            
        remaining_quality = root_match.group(2).strip().upper()

        # Clean up remaining quality string (remove spaces, dots, and "ADDX")
        clean_quality = remaining_quality.replace(' ', '').replace('.', '')
        clean_quality = re.sub(r'ADD\d+', '', clean_quality)
        
        # Try direct match first with dynamic aliases
        standardized_quality = self.aliases.get(clean_quality, None)
        if standardized_quality:
            return root_note, standardized_quality

        # Try to find a quality that is a substring of the remaining_quality
        for key, value in sorted(self.aliases.items(), key=lambda x: len(x[0]), reverse=True):
            if key and clean_quality.startswith(key):
                return root_note, value

        # Fallback for simple major if no quality is specified
        if not clean_quality:
            return root_note, 'Major'

        print(f"Warning: Could not determine quality for {original_chord_name}. Using Major.")
        return root_note, 'Major'

    def _get_fret_for_note_on_string(self, target_note, open_string_note):
        target_note_index = self.notes.index(target_note)
        open_string_note_index = self.notes.index(open_string_note)
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
                target_root = self.enharmonics.get(root_note, root_note)
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
                     # Normalize flats to sharps for lookup
                     lookup_note = self.enharmonics.get(root_note, root_note)
                     
                     if lookup_note in self.notes:
                         current_idx = self.notes.index(lookup_note)
                         new_idx = (current_idx + sub["root_offset"]) % 12
                         root_note = self.notes[new_idx]
                         print(f"  Root shifted by {sub['root_offset']} to {root_note}")
                break

        if quality not in self.chord_data:
            # Fallback mappings for jazz styles if quality is missing
            if quality in self.fallbacks:
                new_quality = self.fallbacks[quality]
                print(f"Chord quality '{quality}' missing. Falling back to '{new_quality}' for {chord_name}")
                quality = new_quality
            
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
