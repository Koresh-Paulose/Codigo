import re

with open('backend/features/teach/student_agent/llm_client.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Move concept extraction up
concept_extraction = r'''        # Extract target concept, fact grounding, and question progress
        concept_match = re.search(r"TARGET TOPIC:\s*([^\n\r]+)", system_prompt)
        current_concept = concept_match.group(1).strip() if concept_match else "this topic"

        fact_match = re.search(r"FACT GROUNDING:\s*([^\n\r]+)", system_prompt)
        current_fact = fact_match.group(1).strip() if fact_match else ""

        progress_match = re.search(r"SESSION PROGRESS:\s*Question (\d+) of (\d+)", system_prompt)
        q_num = int(progress_match.group(1)) if progress_match else 1
        total_q = int(progress_match.group(2)) if progress_match else 5

        is_opening = (q_num == 1) or ("opening question" in user_prompt.lower())
        f_low = (current_concept + " " + current_fact).lower()'''

# Remove it from its current position
code = re.sub(r'\s*# Extract target concept, fact grounding, and question progress.*?(?=# Handle Opening Question 1)', '\n\n', code, flags=re.DOTALL)

# Insert it at the top of _generate_simulated_response
code = code.replace(
    'is_evaluation = "PEDAGOGICAL_EVALUATOR_ENGINE" in system_prompt\n',
    'is_evaluation = "PEDAGOGICAL_EVALUATOR_ENGINE" in system_prompt\n\n' + concept_extraction + '\n'
)

# 2. Add f_low checks to evaluation elifs
code = code.replace('elif any(w in exp_low for w in ["technology", "tech"', 'elif re.search(r\'\\\\b(human|humans|homo sapiens)\\\\b\', f_low) and any(w in exp_low for w in ["technology", "tech"')
code = code.replace('elif "climb surface" in exp_low or', 'elif re.search(r\'\\\\b(cat|cats|felis)\\\\b\', f_low) and ("climb surface" in exp_low or')
code = code.replace('elif "digest" in exp_low and', 'elif re.search(r\'\\\\b(cat|cats|felis)\\\\b\', f_low) and "digest" in exp_low and')
code = code.replace('elif "aware" in exp_low or', 'elif re.search(r\'\\\\b(cat|cats|felis)\\\\b\', f_low) and ("aware" in exp_low or')
code = code.replace('elif "sharpen" in exp_low and', 'elif re.search(r\'\\\\b(cat|cats|felis)\\\\b\', f_low) and "sharpen" in exp_low and')
code = code.replace('elif "feel" in exp_low or', 'elif re.search(r\'\\\\b(cat|cats|felis)\\\\b\', f_low) and ("feel" in exp_low or')
code = code.replace('elif "releases the blood" in exp_low or', 'elif re.search(r\'\\\\b(respiratory|circulatory|oxygen)\\\\b\', f_low) and ("releases the blood" in exp_low or')
code = code.replace('elif any(w in exp_low for w in ["red blood",', 'elif re.search(r\'\\\\b(respiratory|circulatory|oxygen)\\\\b\', f_low) and any(w in exp_low for w in ["red blood",')
code = code.replace('elif any(w in exp_low for w in ["animal", "animal kingdom"', 'elif re.search(r\'\\\\b(human|humans|homo sapiens)\\\\b\', f_low) and any(w in exp_low for w in ["animal", "animal kingdom"')
code = code.replace('elif any(w in exp_low for w in ["cell", "tissue", "organ"', 'elif re.search(r\'\\\\b(body|cell|organ|tissue)\\\\b\', f_low) and any(w in exp_low for w in ["cell", "tissue", "organ"')
code = code.replace('elif any(w in exp_low for w in ["need", "food", "water"', 'elif re.search(r\'\\\\b(human|humans|homo sapiens)\\\\b\', f_low) and any(w in exp_low for w in ["need", "food", "water"')
code = code.replace('elif any(w in exp_low for w in ["diversity", "culture"', 'elif re.search(r\'\\\\b(human|humans|homo sapiens)\\\\b\', f_low) and any(w in exp_low for w in ["diversity", "culture"')


# 3. Add f_low checks to student reaction elifs
code = code.replace('elif any(w in t_low for w in ["technology", "tech"', 'elif re.search(r\'\\\\b(human|humans|homo sapiens)\\\\b\', f_low) and any(w in t_low for w in ["technology", "tech"')
code = code.replace('elif "climb surface" in t_low or', 'elif re.search(r\'\\\\b(cat|cats|felis)\\\\b\', f_low) and ("climb surface" in t_low or')
code = code.replace('elif "digest" in t_low or', 'elif re.search(r\'\\\\b(cat|cats|felis)\\\\b\', f_low) and ("digest" in t_low or')
code = code.replace('elif "aware" in t_low or', 'elif re.search(r\'\\\\b(cat|cats|felis)\\\\b\', f_low) and ("aware" in t_low or')
code = code.replace('elif "sharpen" in t_low and', 'elif re.search(r\'\\\\b(cat|cats|felis)\\\\b\', f_low) and "sharpen" in t_low and')
code = code.replace('elif "feel" in t_low or', 'elif re.search(r\'\\\\b(cat|cats|felis)\\\\b\', f_low) and ("feel" in t_low or')
code = code.replace('elif any(w in t_low for w in ["red blood",', 'elif re.search(r\'\\\\b(respiratory|circulatory|oxygen)\\\\b\', f_low) and any(w in t_low for w in ["red blood",')
code = code.replace('elif any(w in t_low for w in ["animal", "animal kingdom"', 'elif re.search(r\'\\\\b(human|humans|homo sapiens)\\\\b\', f_low) and any(w in t_low for w in ["animal", "animal kingdom"')
code = code.replace('elif any(w in t_low for w in ["coordinate", "signal"', 'elif re.search(r\'\\\\b(respiratory|circulatory|oxygen|nervous)\\\\b\', f_low) and any(w in t_low for w in ["coordinate", "signal"')
code = code.replace('elif any(w in t_low for w in ["cell", "tissue", "organ"', 'elif re.search(r\'\\\\b(body|cell|organ|tissue)\\\\b\', f_low) and any(w in t_low for w in ["cell", "tissue", "organ"')
code = code.replace('elif any(w in t_low for w in ["social", "community"', 'elif re.search(r\'\\\\b(human|humans|homo sapiens)\\\\b\', f_low) and any(w in t_low for w in ["social", "community"')
code = code.replace('elif any(w in t_low for w in ["need", "food", "water"', 'elif re.search(r\'\\\\b(human|humans|homo sapiens)\\\\b\', f_low) and any(w in t_low for w in ["need", "food", "water"')
code = code.replace('elif any(w in t_low for w in ["diversity", "culture"', 'elif re.search(r\'\\\\b(human|humans|homo sapiens)\\\\b\', f_low) and any(w in t_low for w in ["diversity", "culture"')
code = code.replace('elif any(w in t_low for w in ["surviv", "evolv"', 'elif re.search(r\'\\\\b(human|humans|homo sapiens)\\\\b\', f_low) and any(w in t_low for w in ["surviv", "evolv"')


with open('backend/features/teach/student_agent/llm_client.py', 'w', encoding='utf-8') as f:
    f.write(code)
print('Done!')
