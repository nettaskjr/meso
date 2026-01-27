
import os
import re

def clean_empty_links(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    in_material_section = False
    
    for line in lines:
        if "**Material para Download:**" in line:
            in_material_section = True
            new_lines.append(line)
            continue
        
        if in_material_section:
            # Check if line is a list item with an empty link
            if re.match(r'^\s*-\s+\[.*\]\(\)\s*$', line):
                continue
            # If we hit the next section (##), stop tracking
            if line.startswith('##'):
                in_material_section = False
        
        new_lines.append(line)
        
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

files = [
    'depigmentation.md', 'dmae.md', 'mesotox.md', 
    'NCTC.md', 'silicio.md', 'vitaminac.md', 'xdna.md', 'glutathion.md'
]

for f in files:
    if os.path.exists(f):
        clean_empty_links(f)
        print(f"Limpo: {f}")
