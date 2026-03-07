import math

def calculate_transition_cost(voicing1, voicing2):
    # Calculates the cost of transitioning between two chord voicings.
    # The cost is the sum of the distances each finger travels.

    # Assumes voicings are dictionaries with a 'frets' key.
    # A value of -1 or 'x' can represent a muted string.
    cost = 0
    for fret1, fret2 in zip(voicing1['frets'], voicing2['frets']):
        # Ignore muted strings in the calculation
        if isinstance(fret1, int) and isinstance(fret2, int) and fret1 >= 0 and fret2 >= 0:
            cost += abs(fret1 - fret2)
    return cost

def find_optimal_progression(parsed_chords, chord_library_instance):
    # This function finds the optimal chord progression.
    # It uses a dynamic programming approach (Viterbi algorithm).

    print("\n--- Optimization Process ---")

    # List of lists of valid voicings for each chord
    all_voicing_options = []
    for chord_event in parsed_chords:
        voicings = chord_library_instance.get_chord_voicings(chord_event['name'])
        all_voicing_options.append(voicings)
        if not voicings:
            print(f"Warning: Chord {chord_event['name']} not found or has no voicings. Skipping.")

    valid_indices = [i for i, voicings in enumerate(all_voicing_options) if voicings]
    
    if not valid_indices:
        print("Error: No valid chords found in the progression.")
        return [None] * len(parsed_chords)
        
    dp = [] # dp[step][j] = (min_cost, prev_j)
    
    # Initialize first valid chord
    first_idx = valid_indices[0]
    dp.append([(0, None) for _ in all_voicing_options[first_idx]])
    
    for step in range(1, len(valid_indices)):
        prev_idx = valid_indices[step - 1]
        curr_idx = valid_indices[step]
        
        prev_options = all_voicing_options[prev_idx]
        curr_options = all_voicing_options[curr_idx]
        
        curr_dp_row = []
        for j, curr_voicing in enumerate(curr_options):
            min_cost = float('inf')
            best_prev_j = -1
            
            for prev_j, prev_voicing in enumerate(prev_options):
                transition_cost = calculate_transition_cost(prev_voicing, curr_voicing)
                total_cost = dp[step - 1][prev_j][0] + transition_cost
                
                if total_cost < min_cost:
                    min_cost = total_cost
                    best_prev_j = prev_j
                    
            curr_dp_row.append((min_cost, best_prev_j))
            
        dp.append(curr_dp_row)
        
    # Backtrack to find the optimal path
    optimal_path_indices = []
    
    # Find minimum cost in the last step
    min_total_cost = float('inf')
    best_last_j = -1
    for j, (cost, _) in enumerate(dp[-1]):
        if cost < min_total_cost:
            min_total_cost = cost
            best_last_j = j
            
    print(f"Optimal Total Cost: {min_total_cost}")
    
    curr_j = best_last_j
    for step in range(len(valid_indices) - 1, -1, -1):
        optimal_path_indices.append(curr_j)
        if step > 0:
            curr_j = dp[step][curr_j][1]
            
    optimal_path_indices.reverse()
    
    # Map back to the original array
    optimal_voicings = [None] * len(parsed_chords)
    for step, orig_idx in enumerate(valid_indices):
        chosen_j = optimal_path_indices[step]
        optimal_voicings[orig_idx] = all_voicing_options[orig_idx][chosen_j]
        
    return optimal_voicings

def get_all_note_positions(note_name):
    # 0: 'e', 1: 'B', 2: 'G', 3: 'D', 4: 'A', 5: 'E'
    string_notes = [64, 59, 55, 50, 45, 40] 
    
    from music21 import pitch
    try:
        p = pitch.Pitch(note_name)
        midi = p.ps
    except:
        return []
        
    positions = []
    for i, open_midi in enumerate(string_notes):
        fret = int(midi - open_midi)
        if 0 <= fret <= 15:
            positions.append({'string_idx': i, 'fret': fret})
            
    return positions

def calculate_melody_transition_cost(pos1, pos2):
    # Cost function for melody transitions
    # Penalizes large fret jumps heavily, and smaller string jumps moderately
    fret_dist = abs(pos1['fret'] - pos2['fret'])
    string_dist = abs(pos1['string_idx'] - pos2['string_idx'])
    
    # Heuristic: fret distance is primary, string distance is secondary
    return (fret_dist * 5) + (string_dist * 2)

def find_optimal_melody_path(melody_events):
    # Finds the optimal sequence of (string, fret) positions for a melody
    # using the Viterbi algorithm to minimize hand movement.
    
    note_events = [e for e in melody_events if e['type'] == 'note']
    if not note_events:
        return []
        
    all_options = []
    for event in note_events:
        options = get_all_note_positions(event['name'])
        all_options.append(options)
        
    # Standard Viterbi DP
    dp = [] # dp[step][j] = (min_cost, prev_j)
    
    # Initialize first note
    if not all_options[0]:
        # Handle case where first note has no valid positions
        dp.append([(0, None)])
    else:
        dp.append([(0, None) for _ in all_options[0]])
        
    for step in range(1, len(all_options)):
        curr_options = all_options[step]
        prev_options = all_options[step - 1]
        
        if not curr_options:
            # If no options for current note, carry over min cost from prev step
            dp.append([(dp[step-1][0][0], 0)])
            continue
            
        curr_dp_row = []
        for j, curr_pos in enumerate(curr_options):
            min_cost = float('inf')
            best_prev_j = -1
            
            for prev_j, prev_pos in enumerate(prev_options):
                if not prev_pos: # Handle placeholder from previous missing note
                    transition_cost = 0
                else:
                    transition_cost = calculate_melody_transition_cost(prev_pos, curr_pos)
                    
                total_cost = dp[step - 1][prev_j][0] + transition_cost
                
                if total_cost < min_cost:
                    min_cost = total_cost
                    best_prev_j = prev_j
                    
            curr_dp_row.append((min_cost, best_prev_j))
        dp.append(curr_dp_row)
        
    # Backtrack
    optimal_path_indices = []
    min_total_cost = float('inf')
    best_last_j = 0
    
    for j, (cost, _) in enumerate(dp[-1]):
        if cost < min_total_cost:
            min_total_cost = cost
            best_last_j = j
            
    curr_j = best_last_j
    for step in range(len(all_options) - 1, -1, -1):
        optimal_path_indices.append(curr_j)
        curr_j = dp[step][curr_j][1]
        if curr_j is None: break
            
    optimal_path_indices.reverse()
    
    # Return list of chosen (string_idx, fret) for EACH note event
    results = []
    for step, j in enumerate(optimal_path_indices):
        if all_options[step]:
            results.append(all_options[step][j])
        else:
            results.append(None)
            
    return results