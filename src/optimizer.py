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
    # It uses a dynamic programming approach (Viterbi-like algorithm).

    print("\n--- Optimization Process ---")

    optimal_voicings = [None] * len(parsed_chords)
    dp = []
    paths = []

    # Prepare a list of actual voicings, or None if not found
    actual_voicings_for_progression = []
    for chord_event in parsed_chords:
        voicing = chord_library_instance.get_chord_voicing(chord_event['name'])
        actual_voicings_for_progression.append(voicing)

    first_valid_chord_idx = -1
    for i, voicing in enumerate(actual_voicings_for_progression):
        if voicing:
            first_valid_chord_idx = i
            break
    
    if first_valid_chord_idx == -1:
        print("Error: No valid chords found in the progression.")
        return optimal_voicings

    # Initialize for the first valid chord
    first_chord_voicings_list = [actual_voicings_for_progression[first_valid_chord_idx]]
    dp.append([(0, None)] * len(first_chord_voicings_list))
    paths.append([[0]]) # Only one voicing for the first valid chord
    optimal_voicings[first_valid_chord_idx] = first_chord_voicings_list[0]

    # Iterate through the rest of the chords
    for i in range(first_valid_chord_idx + 1, len(parsed_chords)):
        current_voicing_option = actual_voicings_for_progression[i]
        
        if not current_voicing_option:
            print(f"Warning: Chord {parsed_chords[i]['name']} not found in library. Skipping.")
            dp.append(dp[-1])
            paths.append(paths[-1])
            continue

        # Find the last valid previous chord to calculate transition cost
        prev_valid_idx = i - 1
        while prev_valid_idx >= first_valid_chord_idx and not actual_voicings_for_progression[prev_valid_idx]:
            prev_valid_idx -= 1
        
        if prev_valid_idx < first_valid_chord_idx: # Should not happen if first_valid_chord_idx is set
            # This means all previous chords were invalid, so we just take the current one with 0 cost
            current_dp_row = [(0, None)]
            current_paths_row = [[0]]
        else:
            prev_voicing_option = actual_voicings_for_progression[prev_valid_idx]
            
            current_dp_row = []
            current_paths_row = []

            min_cost = float('inf')
            best_prev_idx = -1

            # Since we only have one voicing per chord for now, k will always be 0
            transition_cost = calculate_transition_cost(prev_voicing_option, current_voicing_option)
            total_cost = dp[-1][0][0] + transition_cost

            if total_cost < min_cost:
                min_cost = total_cost
                best_prev_idx = 0 # Index within the single-element prev_voicing_option list
            
            current_dp_row.append((min_cost, best_prev_idx))
            current_paths_row.append(paths[-1][best_prev_idx] + [0]) # 0 because only one voicing option
        
        dp.append(current_dp_row)
        paths.append(current_paths_row)
        optimal_voicings[i] = current_voicing_option

    # Find the overall minimum cost path in the last row
    if dp and dp[-1]:
        last_row_costs = [item[0] for item in dp[-1]]
        min_total_cost = float('inf')
        best_last_voicing_idx = -1

        for idx, cost in enumerate(last_row_costs):
            if cost < min_total_cost:
                min_total_cost = cost
                best_last_voicing_idx = idx

        if best_last_voicing_idx != -1:
            print(f"Optimal Total Cost: {min_total_cost}")

    return optimal_voicings