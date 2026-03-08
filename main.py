import argparse

from src.parser import parse_score_file
from src.chords import ChordLibrary
from src.optimizer import find_optimal_progression, find_optimal_melody_path
from src.tablature import generate_tablature
from src.exporter import export_to_musicxml

def main():
    """Main entry point for the Jaso application."""
    parser = argparse.ArgumentParser(description='Generate guitar tablature from MusicXML files.')
    parser.add_argument('musicxml_file', type=str, help='The path to the input MusicXML file (.musicxml, .xml, .mxl).')
    parser.add_argument('--flavor', type=str, choices=['classical', 'freddie', 'gypsy'], default='classical', help='The jazz playing style flavor to generate chords for (classical, freddie, or gypsy). Default is classical.')
    # Maintain backward compatibility: if they pass a JSON file, we'll try to use it as the flavor
    parser.add_argument('output_file', type=str, help='The path for the output tablature file.')
    parser.add_argument('--xml', type=str, help='Optional path to export optimized MusicXML for MuseScore.')
    
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

    # 1. Parse the input score (MusicXML or LilyPond)
    melody, chords, sections, score = parse_score_file(args.musicxml_file)
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

    # 4. Find the optimal melody path
    optimal_melody_fingerings = find_optimal_melody_path(melody)

    # 5. Determine pickup measure length from the score
    pickup_length = 0.0
    if score and score.parts:
        first_measure = score.parts[0].getElementsByClass('Measure')[0]
        if first_measure.quarterLength < 4.0:  # shorter than a full measure = pickup
            pickup_length = first_measure.quarterLength

    # 6. Generate the text tablature
    generate_tablature(melody, chords, sections, optimal_progression, optimal_melody_fingerings, actual_output, pickup_length)

    # 7. Export to MusicXML if requested
    if args.xml:
        export_to_musicxml(score, melody, optimal_melody_fingerings, chords, optimal_progression, args.xml, pickup_length)

if __name__ == '__main__':
    main()