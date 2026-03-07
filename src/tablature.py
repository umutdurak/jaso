import re

def generate_tablature(melody_events, parsed_chords, sections, optimal_chord_voicings, output_file):
    # Generates the tablature and writes it to the output file.

    ordered_strings = ['e', 'B', 'G', 'D', 'A', 'E']

    # --- Timeline Creation ---
    timeline = []
    
    # Calculate implied duration by checking distance to next chord
    for i, chord in enumerate(parsed_chords):
        if optimal_chord_voicings[i]:
            start_time = chord.get('time', 0.0)
            
            # Determine how long this chord lasts (until the next chord starts)
            if i < len(parsed_chords) - 1:
                next_start = parsed_chords[i+1].get('time', start_time)
                implied_duration = next_start - start_time
            else:
                # Default for the very last chord
                implied_duration = 4.0 

            timeline.append({
                'time': start_time,
                'type': 'chord',
                'duration': implied_duration,
                'name': chord['name'],
                'voicing': optimal_chord_voicings[i]
            })

    # Add lyrics to timeline from melody_events
    if melody_events:
        for event in melody_events:
            if event.get('lyric'):
                timeline.append({
                    'time': event['time'],
                    'type': 'lyric',
                    'text': event['lyric'],
                    'duration': event['duration']
                })
            
    # Add sections to timeline
    if sections:
        for section in sections:
            timeline.append({
                'time': section['time'],
                'type': 'section',
                'name': section['name'],
                'duration': 0.0
            })

    timeline.sort(key=lambda x: x['time'])

    print("--- Timeline Debug ---")
    for t in timeline:
        if t['type'] == 'chord':
            print(f"Chord: {t['name']:<15} Time: {t['time']:<5} Duration: {t['duration']}")
        elif t['type'] == 'section':
            print(f"Section: {t['name']:<13} Time: {t['time']:<5}")

    # --- Tablature Generation ---
    CHAR_PER_QUARTER_NOTE = 4 # 1/16th note resolution. 2 digits is 1/8th note width.
    BEATS_PER_MEASURE = 4
    MEASURES_PER_LINE = 4

    total_duration = max(event['time'] + event['duration'] for event in timeline) if timeline else 0
    num_measures = int(total_duration / BEATS_PER_MEASURE) + 1

    output_lines = ["--- Chord Tablature ---"]

    for line_start_measure in range(0, num_measures, MEASURES_PER_LINE):
        line_end_measure = min(line_start_measure + MEASURES_PER_LINE, num_measures)
        
        line_section = ""
        line_chords = "Chords: "
        line_tab = {s: f"{s.upper()}:    " for s in ordered_strings}
        line_lyrics = "Lyrics: "

        for m in range(line_start_measure, line_end_measure):
            measure_start_time = m * BEATS_PER_MEASURE
            measure_end_time = (m + 1) * BEATS_PER_MEASURE
            measure_width = CHAR_PER_QUARTER_NOTE * BEATS_PER_MEASURE

            measure_tab_grid = {s: ['-'] * measure_width for s in ordered_strings}
            measure_chords_grid = [' '] * measure_width
            measure_lyrics_grid = [' '] * measure_width
            
            # Print sections
            for event in timeline:
                if event['type'] == 'section' and measure_start_time <= event['time'] < measure_end_time:
                    line_section += f"[{event['name']}] "
                    
            for event in timeline:
                if measure_start_time <= event['time'] < measure_end_time:
                    pos = int((event['time'] - measure_start_time) * CHAR_PER_QUARTER_NOTE)
                    
                    if event['type'] == 'chord':
                        chord_name = event['name']
                        for i, char in enumerate(chord_name):
                            if pos + i < measure_width:
                                measure_chords_grid[pos + i] = char

                        voicing = event['voicing']
                        for i, s_name in enumerate(ordered_strings):
                            fret = voicing['frets'][i]
                            fret_str = str(fret) if fret != -1 else 'x'
                            
                            # Insert the fret string character by character 
                            for char_idx, char in enumerate(fret_str):
                                if pos + char_idx < measure_width:
                                    measure_tab_grid[s_name][pos + char_idx] = char
                                    
                    elif event['type'] == 'lyric':
                        lyric_text = event['text']
                        for i, char in enumerate(lyric_text):
                            if pos + i < measure_width:
                                measure_lyrics_grid[pos + i] = char

            line_chords += "|" + "".join(measure_chords_grid)
            for s in ordered_strings:
                line_tab[s] += "|" + "".join(measure_tab_grid[s])
            line_lyrics += "|" + "".join(measure_lyrics_grid)

        output_lines.append("")
        if line_section.strip():
            output_lines.append("        " + line_section.strip())
        output_lines.append(line_chords + "|")
        for s in ordered_strings:
            output_lines.append(line_tab[s] + "|")
            
        # Only print lyrics if there are actual lyrics present in this line
        if any(c != ' ' and c != '|' for c in line_lyrics[8:]):
             output_lines.append(line_lyrics + "|")

    # --- Chord Diagrams ---
    chord_diagrams = "\n--- Chord Voicing Details ---\n"
    for i, voicing in enumerate(optimal_chord_voicings):
        if voicing:
            chord_diagrams += f"\nChord {i+1} ({parsed_chords[i]['name']})\n"
            for j, s_name in enumerate(ordered_strings):
                fret = voicing['frets'][j]
                fret_str = str(fret) if fret != -1 else 'x'
                # Format to look like a clean vertical box: E |---7---|
                # We pad the fret number to always take 2 spaces so things align 
                fret_padded = fret_str.ljust(2, '-')
                chord_diagrams += f"{s_name.upper()} |---{fret_padded}---|\n"

    # --- Write to File ---
    with open(output_file, 'w') as f:
        f.write("\n".join(output_lines))
        f.write(chord_diagrams)

    print(f"Tablature generated and saved to {output_file}")
