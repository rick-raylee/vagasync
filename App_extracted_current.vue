import json
import re
import os

log_path = r"C:\Users\ricar\.gemini\antigravity\brain\02f133c6-224a-4dfe-b36f-b63da66bb036\.system_generated\logs\transcript_full.jsonl"
out_path = r"C:\Users\ricar\Desktop\VAGASYNC\App_extracted.vue"

largest_size = 0
largest_content = ""

if os.path.exists(log_path):
    with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
        for idx, line in enumerate(f):
            # Search for any large blocks in the json line
            matches = re.findall(r'<script setup>[\s\S]*?<\/template>', line)
            for m in matches:
                # Unescape if it's inside a JSON string
                # We can try to decode the JSON if we find a match
                size = len(m)
                if size > largest_size:
                    largest_size = size
                    largest_content = m
                    print(f"Found match of size {size} at line {idx}")

    if largest_content:
        # Sometimes there are escaped characters like \n, \", etc.
        # Let's try to unescape it by parsing it as a JSON string if possible, or using python's unicode_escape
        try:
            # Let's wrap it in double quotes and load it as JSON
            decoded = json.loads('"' + largest_content.replace('"', '\\"') + '"')
            # wait, if it's already got escapes, we want to decode the actual json line first to get the raw string
            # Let's find the exact JSON object for the line
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                for idx, line in enumerate(f):
                    if idx == idx: # we want the line we found
                        try:
                            obj = json.loads(line)
                            # search inside obj recursively for App.vue content
                            def search_dict(d):
                                global largest_size, largest_content
                                if isinstance(d, dict):
                                    for k, v in d.items():
                                        if isinstance(v, str) and "<script setup>" in v and "</template>" in v:
                                            if len(v) > largest_size:
                                                largest_size = len(v)
                                                largest_content = v
                                        else:
                                            search_dict(v)
                                elif isinstance(d, list):
                                    for item in d:
                                        search_dict(item)
                            search_dict(obj)
                        except:
                            pass
        except Exception as e:
            print("Decoding error:", e)
            
        with open(out_path, 'w', encoding='utf-8') as out:
            out.write(largest_content)
        print(f"Successfully wrote {len(largest_content)} characters to {out_path}")
else:
    print("Log not found")
