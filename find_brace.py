import re

with open('static/js/script.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Find where { and } are unbalanced — track depth line by line
depth = 0
lines = content.split('\n')
suspicious = []
for i, line in enumerate(lines, 1):
    for ch in line:
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth < 0:
                suspicious.append((i, 'EXTRA } at depth -1', line.strip()))
                depth = 0  # reset to continue

print('Final depth (should be 0):', depth)
print('Suspicious lines:', suspicious)
if not suspicious:
    print('Searching for last 5 lines with braces...')
    for i, line in enumerate(lines, 1):
        if '}' in line and i > len(lines) - 50:
            print(f'  Line {i}: {line.rstrip()}')
