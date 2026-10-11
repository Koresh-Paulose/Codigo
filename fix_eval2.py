with open('backend/features/teach/student_agent/llm_client.py', 'r', encoding='utf-8') as f:
    code = f.read()

code = code.replace(r"r'\\b", r"r'\b").replace(r"\\b'", r"\b'")

# Also fix the syntax error introduced on line 124: `("climb surface" in exp_low or ("climb" in exp_low and length <= 5):` has unbalanced parentheses!
# Let's fix that too.
code = code.replace(r'elif re.search(r\'\b(cat|cats|felis)\b\', f_low) and ("climb surface" in exp_low or ("climb" in exp_low and length <= 5):', r'elif re.search(r\'\b(cat|cats|felis)\b\', f_low) and ("climb surface" in exp_low or ("climb" in exp_low and length <= 5)):')
code = code.replace(r'elif re.search(r\'\b(cat|cats|felis)\b\', f_low) and ("climb surface" in t_low or ("climb" in t_low and ("surface" in t_low or "tree" in t_low or len(t_low.split()) <= 4)):', r'elif re.search(r\'\b(cat|cats|felis)\b\', f_low) and ("climb surface" in t_low or ("climb" in t_low and ("surface" in t_low or "tree" in t_low or len(t_low.split()) <= 4))):')

with open('backend/features/teach/student_agent/llm_client.py', 'w', encoding='utf-8') as f:
    f.write(code)
