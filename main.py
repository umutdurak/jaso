import argparse

from src.parser import parse_musicxml_file
from src.chords import ChordLibrary
from src.optimizer import find_optimal_progression
from src.tablature import generate_tablature

def main():
    """Main entry point for the Jaso application."""
    parser = argparse.ArgumentParser(description='Generate guitar tablature from MusicXML files.')
    parser.add_argument('musicxml_file', type=str, help='The path to the input MusicXML file (.musicxml, .xml, .mxl).')
    parser.add_argument('--flavor', type=str, choices=['classical', 'freddie', 'gypsy'], default='classical', help='The jazz playing style flavor to generate chords for (classical, freddie, or gypsy). Default is classical.')
    # Maintain backward compatibility: if they pass a JSON file, we'll try to use it as the flavor
    parser.add_argument('output_file', type=str, help='The path for the output tablature file.')
    
    # Optional fallback for old usage taking positional JSON
    parser.add_argument('legacy_chords_file', type=str, nargs='?', default=None, help=argparse.SUPPRESS)

    args = parser.parse_args()
    
    # Handle legacy invocations like "python main.py sample.xml chords.json out.txt"
    # In that case, output_file becomes chords.json, and legacy_chords_file becomes out.txt
    actual_output = args.output_file
    chords_source = f"chords_{args.flavor}.json"
    subs_source = f"substitutions_{args.flavor}.json"
    if args.flavor == 'freddie':
        chords_source = "chords_freddie_green.json"
        subs_source = "substitutions_freddie_green.json"
        
    if args.legacy_chords_file:
        if args.output_file.endswith('.json'):
            chords_source = args.output_file
            actual_output = args.legacy_chords_file

    print(f"MusicXML file: {args.musicxml_file}")
    print(f"Chords Source: {chords_source}")
    print(f"Output file: {actual_output}")

    # 1. Parse the MusicXML file
    melody, chords, sections = parse_musicxml_file(args.musicxml_file)
    if melody or chords or sections:
        print("--- Parsed Melody Events (Structured) ---")
        for event in melody:
            print(f"  - {event}")
        print("--- Parsed Chord Events (Structured) ---")
        for event in chords:
            print(f"  - {event}")
        if sections:
            print("--- Parsed Section Events (Structured) ---")
            for event in sections:
                print(f"  - {event}")

    # 2. Load the chord shapes using the new ChordLibrary
    chord_library_instance = ChordLibrary(chords_source, subs_source)
    if chord_library_instance.chord_data:
        print("--- Loaded Chord Library ---")
        for quality, voicings in chord_library_instance.chord_data.items():
            print(f"  - {quality}: {len(voicings)} voicings")

    # 3. Find the optimal chord progression
    optimal_progression = find_optimal_progression(chords, chord_library_instance)

    # 4. Generate the tablature
    generate_tablature(melody, chords, sections, optimal_progression, actual_output)

if __name__ == '__main__':
    main()