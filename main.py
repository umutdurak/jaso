import argparse

def main():
    """Main entry point for the Jaso application."""
    parser = argparse.ArgumentParser(description='Generate guitar tablature from LilyPond files.')
    parser.add_argument('lilypond_file', type=str, help='The path to the input LilyPond file (.ly).')
    parser.add_argument('chords_file', type=str, help='The path to the chord shapes JSON file.')
    parser.add_argument('output_file', type=str, help='The path for the output tablature file.')

    args = parser.parse_args()

    print(f"LilyPond file: {args.lilypond_file}")
    print(f"Chords file: {args.chords_file}")
    print(f"Output file: {args.output_file}")

    # 1. Parse the LilyPond file
    from src.parser import parse_lilypond_file
    melody, chords = parse_lilypond_file(args.lilypond_file)
    if melody or chords:
        print("--- Parsed Melody Events ---")
        for event in melody:
            print(f"  - {event}")
        print("--- Parsed Chord Events ---")
        for event in chords:
            print(f"  - {event}")

    # 2. Load the chord shapes
    from src.chords import load_chord_library
    chord_library = load_chord_library(args.chords_file)
    if chord_library:
        print("--- Loaded Chord Library ---")
        for name, voicings in chord_library.items():
            print(f"  - {name}: {len(voicings)} voicings")

    # 3. Find the optimal chord progression
    from src.optimizer import find_optimal_progression
    optimal_progression = find_optimal_progression(chords, chord_library)

    # 4. Generate the tablature
    from src.tablature import generate_tablature
    generate_tablature(melody, optimal_progression, args.output_file)

if __name__ == '__main__':
    main()
