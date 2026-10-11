with open('backend/features/teach/student_agent/llm_client.py', 'r', encoding='utf-8') as f: code = f.read()
code = code.replace('"surround" in t_low:', '"surround" in t_low):')
with open('backend/features/teach/student_agent/llm_client.py', 'w', encoding='utf-8') as f: f.write(code)
