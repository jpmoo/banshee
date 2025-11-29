#!/usr/bin/env python3
"""Replace 'town' and 'city' with appropriate words in village descriptions."""
import re
import random

# Read the village data file
with open('data_villages.py', 'r') as f:
    content = f.read()

# Track replacements
replacement_count = 0
lines = content.split('\n')
new_lines = []

# Set seed for consistent replacements
random.seed(42)

for line in lines:
    original_line = line
    # Only process lines that are string entries (contain quotes and town/city)
    if '"' in line and ('town' in line.lower() or 'city' in line.lower()):
        # Replace "town" (whole word, case-insensitive)
        if 'town' in line.lower():
            # Replace lowercase "town"
            line = re.sub(r'\btown\b', lambda m: random.choice(['village', 'hamlet', 'settlement', 'community']), line, flags=re.IGNORECASE)
            # Replace capitalized "Town" 
            line = re.sub(r'\bTown\b', lambda m: random.choice(['Village', 'Hamlet', 'Settlement', 'Community']), line)
            # Replace "-town" and "town-"
            line = re.sub(r'-town\b', lambda m: random.choice(['-village', '-hamlet', '-settlement']), line, flags=re.IGNORECASE)
            line = re.sub(r'\btown-', lambda m: random.choice(['village-', 'hamlet-', 'settlement-']), line, flags=re.IGNORECASE)
            
        # Replace "city" (whole word, case-insensitive)
        if 'city' in line.lower():
            line = re.sub(r'\bcity\b', lambda m: random.choice(['settlement', 'village', 'hamlet']), line, flags=re.IGNORECASE)
            line = re.sub(r'\bCity\b', lambda m: random.choice(['Settlement', 'Village', 'Hamlet']), line)
            line = re.sub(r'-city\b', lambda m: random.choice(['-settlement', '-village', '-hamlet']), line, flags=re.IGNORECASE)
            line = re.sub(r'\bcity-', lambda m: random.choice(['settlement-', 'village-', 'hamlet-']), line, flags=re.IGNORECASE)
        
        if line != original_line:
            replacement_count += 1
    
    new_lines.append(line)

# Write back
with open('data_villages.py', 'w') as f:
    f.write('\n'.join(new_lines))

print(f'Replaced {replacement_count} lines containing "town" or "city"')

"""Replace 'town' and 'city' with appropriate words in village descriptions."""
import re
import random

# Read the village data file
with open('data_villages.py', 'r') as f:
    content = f.read()

# Track replacements
replacement_count = 0
lines = content.split('\n')
new_lines = []

# Set seed for consistent replacements
random.seed(42)

for line in lines:
    original_line = line
    # Only process lines that are string entries (contain quotes and town/city)
    if '"' in line and ('town' in line.lower() or 'city' in line.lower()):
        # Replace "town" (whole word, case-insensitive)
        if 'town' in line.lower():
            # Replace lowercase "town"
            line = re.sub(r'\btown\b', lambda m: random.choice(['village', 'hamlet', 'settlement', 'community']), line, flags=re.IGNORECASE)
            # Replace capitalized "Town" 
            line = re.sub(r'\bTown\b', lambda m: random.choice(['Village', 'Hamlet', 'Settlement', 'Community']), line)
            # Replace "-town" and "town-"
            line = re.sub(r'-town\b', lambda m: random.choice(['-village', '-hamlet', '-settlement']), line, flags=re.IGNORECASE)
            line = re.sub(r'\btown-', lambda m: random.choice(['village-', 'hamlet-', 'settlement-']), line, flags=re.IGNORECASE)
            
        # Replace "city" (whole word, case-insensitive)
        if 'city' in line.lower():
            line = re.sub(r'\bcity\b', lambda m: random.choice(['settlement', 'village', 'hamlet']), line, flags=re.IGNORECASE)
            line = re.sub(r'\bCity\b', lambda m: random.choice(['Settlement', 'Village', 'Hamlet']), line)
            line = re.sub(r'-city\b', lambda m: random.choice(['-settlement', '-village', '-hamlet']), line, flags=re.IGNORECASE)
            line = re.sub(r'\bcity-', lambda m: random.choice(['settlement-', 'village-', 'hamlet-']), line, flags=re.IGNORECASE)
        
        if line != original_line:
            replacement_count += 1
    
    new_lines.append(line)

# Write back
with open('data_villages.py', 'w') as f:
    f.write('\n'.join(new_lines))

print(f'Replaced {replacement_count} lines containing "town" or "city"')

