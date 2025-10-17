import pandas as pd
import numpy as np
from difflib import Differ

def segment(essay_student):
    essay_in_segments = []
    if not essay_student.empty:
        segments = segment_essay(essay_student)
        total_text = ""
        k = 1
        for segment in segments:
            r = get_text_from_segments(segment, total_text)

            segment_text = r['text_segment']
            text_written = r['total_segment']
            total_text = r['final_text']
            start_time = segment.iloc[0]['save_time']
            end_time = segment.iloc[-1]['save_time']
            deleted = r['deleted']
            if(segment_text != ""):
                essay_in_segments.append({
                    'cluster_nr':k,
                    'label':"",
                    'segment': segment_text,
                    'text_written': text_written,
                    'total_essay': total_text,
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration': end_time,
                    'includes_deletion': deleted,
                    'has_pasted_text': False,
                })
                k =k+ 1
    data = pd.DataFrame(essay_in_segments)
    return data

def segment_essay(essay):
    
    #get time between keystrokes
    essay['time_to_next'] = essay['save_time'].shift(-1) - essay['save_time']
    split_indices = list(np.where(essay['time_to_next'] > 3000)[0])

    if not split_indices or split_indices[0] != 0:
            split_indices = [0] + split_indices
    split_indices = split_indices + [essay.shape[0]]

    # Create segments
    segments = []
    for i in range(1, len(split_indices)):
        start = split_indices[i - 1]
        end = split_indices[i]
        segments.append(essay.iloc[start:end])
    
    return segments

def find_difference(start, current):
    d = Differ()
    diff = list(d.compare(start, current))  
    added = [char[2:] for char in diff if char.startswith('+ ')]
    removed = [char[2:] for char in diff if char.startswith('- ')]
    return {"added": "".join(added), "removed": "".join(removed)}


def get_text(difference):
    text_segment = ""
    deleted_text = ""
    for row in difference:
        if row["removed"]:
                    deleted_text = row['removed'] + deleted_text
        if row["added"]:
                    
                    if deleted_text != "":
                            text_segment += f"[Deleted:{deleted_text}]"
                    text_segment += f"{row['added']}"
                    deleted_text = ""
                            
    

    return text_segment

def get_text_from_segments(segment, start_text):
    start = start_text
    difference = []
    for index, row in segment.iterrows():
        current = row["essay_content"]
        difference.append(find_difference(start, current))
        start = current

    total_difference = []
    total_difference.append(find_difference(start_text, current))

    text_segment = get_text(difference)
    total_segment = get_text(total_difference)
    difference = pd.DataFrame(difference)
    all_empty = difference['removed'].isna() | (difference['removed'] == '')
    any_non_empty_values = not all_empty.all() 
    return({"text_segment": text_segment, "total_segment": total_segment, "final_text": current, 'deleted': any_non_empty_values })



