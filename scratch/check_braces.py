def check_braces(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    stack = []
    pairs = {'{': '}', '[': ']', '(': ')'}
    for i, char in enumerate(content):
        if char in pairs:
            stack.append((char, i))
        elif char in pairs.values():
            if not stack:
                return f"Extra closing brace '{char}' at index {i}"
            opening, pos = stack.pop()
            if pairs[opening] != char:
                return f"Mismatched brace '{char}' at index {i}, matches '{opening}' from index {pos}"
    
    if stack:
        opening, pos = stack.pop()
        return f"Unclosed brace '{opening}' at index {pos}"
    
    return "No brace issues found"

print(check_braces(r'c:\Users\hamza zourkane\Downloads\projet-memoire-main\projet-memoire-main\static\js\script.js'))
