def get_hint_prompt(level: int, concept: str, source_chunk: str, user_last_answer: str) -> str:
    """Generate a dynamic hint prompt that evaluates correctness and provides hints based on user input."""

    context_section = ""
    if source_chunk:
        context_section = f"\n\nREFERENCE MATERIAL:\n{source_chunk}\n"

    answer_section = ""
    eval_instruction = ""
    if user_last_answer:
        answer_section = f"\n\nThe student's most recent answer was: \"{user_last_answer}\"\n"
        eval_instruction = (
            "IMPORTANT: First, evaluate if the student's answer demonstrates a correct understanding of the concept. "
            "If they correctly identified or explained the core idea, your response MUST begin with the exact word [CORRECT] "
            "followed by a brief encouraging message confirming they got it right. "
            "If they are incorrect or partially correct, do NOT use the [CORRECT] tag. Instead, provide a hint that directly addresses their misconception or gap in understanding.\n\n"
        )
    else:
        eval_instruction = "The student has just started. Give them a starting hint.\n\n"

    prompt = (
        f"The student is trying to understand the concept: \"{concept}\".{context_section}{answer_section}\n\n{eval_instruction}"
        f"INSTRUCTIONS FOR YOUR HINT:\n"
        f"- Be extremely dynamic and conversational. Adapt to exactly what the student just said.\n"
        f"- If they made a mistake, gently correct their specific mistake.\n"
        f"- Ask a thought-provoking question that points them in the right direction.\n"
        f"- Use analogies or real-world examples to make it intuitive.\n"
        f"- Reference specific details from the material if available.\n"
        f"- Do NOT reveal the full answer directly unless they are completely lost (level 4).\n"
        f"- Keep your response concise (2-4 sentences max).\n"
        f"- Be encouraging and specific to this exact topic.\n"
    )

    if level >= 4:
        prompt += "- Since the student has struggled for a few turns, provide a full, clear explanation of the concept, but end with a simple check-for-understanding question."

    return prompt
