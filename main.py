import streamlit as st
import json
import random
import copy

def generate_initial_state(num_colors, block_counts, empty_column_sizes, used_empty_slots, marked_trays):
    trays = []
    tray_match_colors = {}
    
    for color, count in enumerate(block_counts, start=1):
        trays.append([color] * count)
    
    empty_trays = [[0] * size for size in empty_column_sizes]
    
    for slots in used_empty_slots:
        if slots in block_counts:
            st.error("❌ Lỗi: `used_empty_slots` có thể tạo điều kiện chiến thắng trong bước 1!")
            return None, None, None
    
    for tray_id in marked_trays.get("match", []):
        if 0 <= tray_id < len(trays):
            tray_match_colors[tray_id] = trays[tray_id][0]
    
    for tray_id in marked_trays.get("holder", []):
        if 0 <= tray_id < len(trays) + len(empty_trays):
            tray_match_colors[tray_id] = -2
    
    return trays, empty_trays, tray_match_colors

def get_possible_moves(trays):
    moves = []
    for i, src in enumerate(trays):
        if all(b == 0 for b in src):
            continue
        for j, dst in enumerate(trays):
            if i != j and dst.count(0) > 0:
                moves.append((i, j))
    return moves

def apply_move(trays, move):
    src, dst = move
    new_trays = copy.deepcopy(trays)
    
    src_blocks = new_trays[src]
    dst_blocks = new_trays[dst]
    
    move_block = None
    for i in range(len(src_blocks) - 1, -1, -1):
        if src_blocks[i] > 0:
            move_block = src_blocks[i]
            src_blocks[i] = 0
            break
    
    if move_block is not None:
        for i in range(len(dst_blocks)):
            if dst_blocks[i] == 0:
                dst_blocks[i] = move_block
                break
    
    return new_trays

def generate_level(num_colors, block_counts, empty_column_sizes, used_empty_slots, marked_trays, num_moves):
    best_trays, best_moves = None, 0
    attempt = 0
    max_attempts = 10
    
    while attempt < max_attempts:
        trays, empty_trays, tray_match_colors = generate_initial_state(
            num_colors, block_counts, empty_column_sizes, used_empty_slots, marked_trays
        )
        if trays is None:
            return None, None, 0
        
        trays.extend(empty_trays)
        actual_moves = 0
        
        for empty_index, slots_to_use in enumerate(used_empty_slots):
            for _ in range(slots_to_use):
                possible_moves = get_possible_moves(trays)
                if not possible_moves:
                    break
                move = random.choice(possible_moves)
                trays = apply_move(trays, move)
                actual_moves += 1
        
        while actual_moves < num_moves:
            possible_moves = get_possible_moves(trays)
            if not possible_moves:
                break
            move = random.choice(possible_moves)
            trays = apply_move(trays, move)
            actual_moves += 1
        
        empty_count = sum(1 for tray in trays if all(b == 0 for b in tray))
        if empty_count != len(empty_column_sizes):
            continue
        
        if actual_moves >= num_moves:
            return trays, tray_match_colors, actual_moves
        
        if actual_moves > best_moves:
            best_trays, best_moves = trays, actual_moves
        
        attempt += 1
    
    return best_trays, tray_match_colors, best_moves

def save_to_json(trays, tray_match_colors):
    level_data = {
        "tray": [
            {
                "trayID": i,
                "trayMatchColorId": tray_match_colors.get(i, None),
                "BlockMarkId": tray
            } for i, tray in enumerate(trays)
        ]
    }
    return json.dumps(level_data, indent=4)

st.title("Game Level Generator")

num_colors = st.number_input("Number of Colors", min_value=1, value=4)
block_counts = st.text_input("Block Counts (comma separated)", "4,4,4,4")
empty_column_sizes = st.text_input("Empty Column Sizes (comma separated)", "4,4")
used_empty_slots = st.text_input("Used Empty Slots (comma separated)", "3,2")
num_moves = st.number_input("Number of Moves", min_value=1, value=50)
marked_trays = st.text_area("Marked Trays (JSON format)", '{"holder": [4,5], "match": [0,2]}')

if st.button("Generate Level"):
    try:
        block_counts = list(map(int, block_counts.split(',')))
        empty_column_sizes = list(map(int, empty_column_sizes.split(',')))
        used_empty_slots = list(map(int, used_empty_slots.split(',')))
        marked_trays = json.loads(marked_trays)
    
        generated_level, tray_match_colors, actual_moves = generate_level(
            num_colors, block_counts, empty_column_sizes, used_empty_slots, marked_trays, num_moves
        )
        
        if generated_level:
            json_output = save_to_json(generated_level, tray_match_colors)
            st.success(f"Level generated with {actual_moves} moves!")
            st.text_area("Generated Level JSON", json_output, height=300)
        else:
            st.error("Failed to generate a valid level. Please check the inputs.")
    except Exception as e:
        st.error(f"Error: {e}")
