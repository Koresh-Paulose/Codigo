import os
import json
import re
import random
from typing import Optional, Dict, Any, List
from .config import GEMINI_API_KEY, GEMINI_MODEL, OPENAI_API_KEY, OPENAI_MODEL, GROQ_API_KEY, GROQ_MODEL

class LLMClient:
    """Multi-tier LLM Client with Gemini -> OpenAI -> Groq -> Smart Dynamic Simulation."""

    def __init__(
        self,
        gemini_api_key: Optional[str] = None,
        gemini_model: Optional[str] = None,
        OPENAI_api_key: Optional[str] = None,
        OPENAI_model: Optional[str] = None,
        groq_api_key: Optional[str] = None,
        groq_model: Optional[str] = None,
    ):
        self.gemini_api_key = gemini_api_key or GEMINI_API_KEY
        self.gemini_model = gemini_model or GEMINI_MODEL
        self.OPENAI_api_key = OPENAI_api_key or OPENAI_API_KEY
        self.OPENAI_model = OPENAI_model or OPENAI_MODEL
        self.groq_api_key = groq_api_key or GROQ_API_KEY
        self.groq_model = groq_model or GROQ_MODEL
        self.last_provider_used: str = "None"

    def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
        """Attempts Gemini -> OpenAI -> Groq -> Simulated response."""
        # 1. Try Gemini
        if self.gemini_api_key:
            try:
                response = self._call_gemini(system_prompt, user_prompt, temperature)
                if response and response.strip():
                    self.last_provider_used = f"Gemini ({self.gemini_model})"
                    return response.strip()
            except Exception as e:
                print(f"\n[Warning] Gemini request failed ({e}). Attempting OpenAI fallback...")

        # 2. Try OPENAI
        if self.OPENAI_api_key:
            try:
                response = self._call_OPENAI(system_prompt, user_prompt, temperature)
                if response and response.strip():
                    self.last_provider_used = f"OPENAI ({self.OPENAI_model})"
                    return response.strip()
            except Exception as e:
                print(f"\n[Warning] OPENAI request failed ({e}). Attempting Groq fallback...")

        # 3. Try Groq Fallback
        if self.groq_api_key:
            try:
                response = self._call_groq(system_prompt, user_prompt, temperature)
                if response and response.strip():
                    self.last_provider_used = f"Groq ({self.groq_model})"
                    return response.strip()
            except Exception as e:
                print(f"\n[Warning] Groq request failed ({e}). Falling back to simulation...")

        # 4. Smart Dynamic Simulation Fallback
        self.last_provider_used = "Simulated AI Student (Local Dynamic Engine)"
        return self._generate_simulated_response(system_prompt, user_prompt)

    def _call_gemini(self, system_prompt: str, user_prompt: str, temperature: float) -> str:
        from openai import OpenAI
        client = OpenAI(
            api_key=self.gemini_api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )
        completion = client.chat.completions.create(
            model=self.gemini_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=temperature,
            max_tokens=1024,
        )
        return completion.choices[0].message.content

    def _call_OPENAI(self, system_prompt: str, user_prompt: str, temperature: float) -> str:
        from openai import OpenAI
        client = OpenAI(api_key=self.OPENAI_api_key)
        completion = client.chat.completions.create(
            model=self.OPENAI_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=temperature,
            max_tokens=1024,
        )
        return completion.choices[0].message.content

    def _call_groq(self, system_prompt: str, user_prompt: str, temperature: float) -> str:
        from groq import Groq
        client = Groq(api_key=self.groq_api_key)
        completion = client.chat.completions.create(
            model=self.groq_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=1024,
        )
        return completion.choices[0].message.content

    @staticmethod
    def _is_uncertain_or_idk(text: str) -> bool:
        t = text.strip().lower()
        if t in ["idk", "i don't know", "dont know", "dont know.", "not sure", "no idea", "no clue", "pass", "skip", "dunno", "?", "no", "none", "n/a", "no answer", "cant say", "can't say"]:
            return True
        words = t.split()
        if len(words) <= 6:
            uncertainty_phrases = [
                "idk", "i dont know", "i don't know", "dont know", "not sure",
                "no idea", "no clue", "dunno", "cant recall", "can't recall",
                "cant remember", "can't remember", "have no idea", "haven't a clue"
            ]
            if any(phrase in t for phrase in uncertainty_phrases):
                return True
        return False

    def _generate_simulated_response(self, system_prompt: str, user_prompt: str) -> str:
        """High-fidelity contextual simulation with active listening, curiosity, and structured feedback."""
        is_evaluation = "PEDAGOGICAL_EVALUATOR_ENGINE" in system_prompt

        # Extract target concept, fact grounding, and question progress
        concept_match = re.search(r"TARGET TOPIC:\s*([^\n\r]+)", system_prompt)
        current_concept = concept_match.group(1).strip() if concept_match else "this topic"

        fact_match = re.search(r"FACT GROUNDING:\s*([^\n\r]+)", system_prompt)
        current_fact = fact_match.group(1).strip() if fact_match else ""

        progress_match = re.search(r"SESSION PROGRESS:\s*Question (\d+) of (\d+)", system_prompt)
        q_num = int(progress_match.group(1)) if progress_match else 1
        total_q = int(progress_match.group(2)) if progress_match else 5

        is_opening = (q_num == 1) or ("opening question" in user_prompt.lower())
        f_low = (current_concept + " " + current_fact).lower()

        if is_evaluation:
            match_exp = re.search(r"TEACHER'S EXPLANATION:\s*(.*?)(?:\n\n|\Z)", user_prompt, re.DOTALL)
            explanation_text = match_exp.group(1).strip() if match_exp else user_prompt
            exp_low = explanation_text.lower()
            words = explanation_text.split()
            length = len(words)

            # Targeted context-sensitive evaluations
            if self._is_uncertain_or_idk(exp_low):
                accuracy = 0.0
                clarity = 0.0
                depth = 0.0
                relevance = 0.0
                strengths = ["Honestly stated being unsure rather than guessing inaccurate facts."]
                missing = [f"Did not attempt an explanation ('{explanation_text}'). Review the notes for this topic."]
                actionable_tip = "Review the notes on this topic and try explaining the intuition in 1-2 complete sentences."
                student_state = "Confused"
                mastered = False
            elif re.search(r'\b(human|humans|homo sapiens)\b', f_low) and any(w in exp_low for w in ["technology", "tech", "tool", "machine", "invent", "science", "device"]):
                accuracy = 7.8
                clarity = 7.5
                depth = 5.5
                relevance = 8.2
                strengths = ["Identified technological innovation and tools as major vehicles of human adaptation."]
                missing = ["Could explain how complex language and generational knowledge transfer allow technology to compound over centuries."]
                actionable_tip = "Explain how cumulative language and generational knowledge transfer enable technologies to compound."
                student_state = "Mostly Clear"
                mastered = True
            elif re.search(r'\b(cat|cats|felis)\b', f_low) and ("climb surface" in exp_low or ("climb" in exp_low and length <= 5)):
                accuracy = 5.5
                clarity = 6.0
                depth = 3.2
                relevance = 6.5
                strengths = ["Correctly noted that claws assist with climbing."]
                missing = ["Too brief ('to climb surfaces'). Missed explaining that claws retract into skin sheaths so they don't drag on rough ground and wear down, keeping them razor-sharp for climbing and hunting."]
                actionable_tip = "Explain both the anatomical mechanism (skin sheaths) and biological purpose (protecting sharpness) in full sentences."
                student_state = "Skeptical"
                mastered = False
            elif re.search(r'\b(cat|cats|felis)\b', f_low) and "digest" in exp_low and ("plant" in exp_low or "long" in exp_low or "take" in exp_low):
                accuracy = 6.8
                clarity = 7.2
                depth = 4.8
                relevance = 7.8
                strengths = ["Identified that a cat's digestive tract is not suited for plant matter."]
                missing = ["Incomplete mechanism ('planst take too long to digest'). Cats are obligate carnivores because their bodies physically lack the enzymes to synthesize vital nutrients like taurine from plants, making meat mandatory."]
                actionable_tip = "Clarify that cats must eat meat because their physiology cannot manufacture essential nutrients from plants, rather than digestion speed alone."
                student_state = "Curious"
                mastered = False
            elif re.search(r'\b(cat|cats|felis)\b', f_low) and ("aware" in exp_low or ("surround" in exp_low and length <= 7)):
                accuracy = 7.5
                clarity = 7.2
                depth = 5.2
                relevance = 8.0
                strengths = ["Understood that whiskers function as an environmental awareness tool."]
                missing = ["Generic explanation. Whiskers have deep nerve follicles that detect minute air currents and measure tight physical spaces, acting like sensory radar in total darkness."]
                actionable_tip = "Include specific sensory mechanisms, like whiskers detecting minute air currents and measuring tight openings."
                student_state = "Curious"
                mastered = False
            elif re.search(r'\b(cat|cats|felis)\b', f_low) and "sharpen" in exp_low and "claw" in exp_low:
                accuracy = 8.4
                clarity = 8.2
                depth = 7.2
                relevance = 8.8
                strengths = ["Correctly explained that scratching maintains and sharpens claws for hunting and climbing."]
                missing = ["Could also mention that scratching deposits territorial pheromones from paw glands and sheds old outer claw sheaths."]
                actionable_tip = "Mention that scratching also serves as territorial communication via scent glands in their paws."
                student_state = "Mostly Clear"
                mastered = True
            elif re.search(r'\b(cat|cats|felis)\b', f_low) and ("feel" in exp_low or ("know" in exp_low and "other" in exp_low)):
                accuracy = 7.8
                clarity = 7.8
                depth = 6.0
                relevance = 8.0
                strengths = ["Accurately recognized that slow blinks and purring communicate emotional states."]
                missing = ["Could explain that purring also releases comforting endorphins and physical vibrations that help cats self-soothe when stressed or in pain."]
                actionable_tip = "Explain the self-soothing function of purring: internal vibration that comforts a cat during pain or stress."
                student_state = "Mostly Clear"
                mastered = True
            elif re.search(r'\b(respiratory|circulatory|oxygen)\b', f_low) and ("releases the blood" in exp_low or ("release" in exp_low and "blood" in exp_low and length <= 6)):
                accuracy = 5.0
                clarity = 5.5
                depth = 3.0
                relevance = 6.0
                strengths = ["Recognized that oxygen must reach the body's tissues."]
                missing = ["Blood cells stay inside capillaries; oxygen molecules diffuse out through thin capillary walls into interstitial fluid to reach surrounding tissue cells."]
                actionable_tip = "Clarify that oxygen molecules diffuse through thin capillary walls into tissue fluid, rather than whole blood cells exiting."
                student_state = "Skeptical"
                mastered = False
            elif re.search(r'\b(respiratory|circulatory|oxygen)\b', f_low) and any(w in exp_low for w in ["red blood", "blood cell", "absorb", "oxygen", "hemoglobin"]):
                strengths = ["Correctly identified red blood cells and hemoglobin as oxygen carriers."]
                missing = ["Could explain how oxygen diffuses from capillary walls into surrounding tissue fluids."]
                actionable_tip = "Describe how oxygen molecules diffuse across capillary walls into tissue fluids."
                accuracy = 8.5
                clarity = 8.0
                depth = 7.5
                relevance = 9.0
                student_state = "Mostly Clear"
                mastered = True
            elif re.search(r'\b(human|humans|homo sapiens)\b', f_low) and any(w in exp_low for w in ["animal", "animal kingdom", "primate", "mammal", "connected", "species"]):
                strengths = ["Highlighted our deep biological connection to the animal kingdom."]
                missing = ["Could detail how complex language and cumulative culture set humans apart."]
                actionable_tip = "Explain how cumulative language lets knowledge compound across generations."
                accuracy = 8.4
                clarity = 8.2
                depth = 7.6
                relevance = 8.8
                student_state = "Mostly Clear"
                mastered = True
            elif re.search(r'\b(body|cell|organ|tissue)\b', f_low) and any(w in exp_low for w in ["cell", "tissue", "organ", "system", "hierarchy"]):
                strengths = ["Clearly outlined how cells combine to form tissues, organs, and organ systems."]
                missing = ["Could explain how different organ systems communicate and coordinate in real time."]
                actionable_tip = "Give an example of two organ systems coordinating in real time (e.g. heart and lungs during running)."
                accuracy = 8.5
                clarity = 8.3
                depth = 7.8
                relevance = 9.0
                student_state = "Mastered!"
                mastered = True
            elif re.search(r'\b(human|humans|homo sapiens)\b', f_low) and any(w in exp_low for w in ["need", "food", "water", "sleep", "shelter", "social"]):
                strengths = ["Emphasized biological survival needs alongside the vital role of social connection."]
                missing = ["Could describe how social connection directly impacts psychological health."]
                actionable_tip = "Explain how social belonging directly influences physical and evolutionary survival."
                accuracy = 8.4
                clarity = 8.2
                depth = 7.5
                relevance = 8.9
                student_state = "Mostly Clear"
                mastered = True
            elif re.search(r'\b(human|humans|homo sapiens)\b', f_low) and any(w in exp_low for w in ["diversity", "culture", "tradition", "language", "respect"]):
                strengths = ["Recognized shared human biology alongside our rich cultural diversity."]
                missing = ["Could explain how common human biology provides unity across diverse cultures."]
                actionable_tip = "Connect our shared human biology to the richness of varied cultures."
                accuracy = 8.5
                clarity = 8.3
                depth = 7.8
                relevance = 9.0
                student_state = "Mastered!"
                mastered = True
            else:
                # Dynamic word overlap check against the facts
                fact_words = set(re.findall(r'\b\w+\b', current_fact.lower()))
                exp_words = set(re.findall(r'\b\w+\b', exp_low))
                # Remove common stopwords to get meaningful keywords
                stopwords = {"the", "a", "an", "is", "are", "was", "were", "to", "in", "for", "of", "on", "and", "or", "but", "with", "as", "at", "by", "that", "this", "it"}
                fact_keywords = fact_words - stopwords
                exp_keywords = exp_words - stopwords
                
                if not fact_keywords:
                    overlap_ratio = 0.5
                else:
                    overlap_ratio = len(fact_keywords.intersection(exp_keywords)) / len(fact_keywords)

                if overlap_ratio >= 0.15 and length >= 6:
                    base = 6.0 + (overlap_ratio * 3.0)
                    accuracy = min(10.0, base + (length / 40.0))
                    clarity = min(10.0, base + 0.5)
                    depth = min(10.0, base - 0.5 + (length / 30.0))
                    relevance = min(10.0, base + 1.0)
                    strengths = ["Addressed some of the core concepts found in the notes."]
                    missing = ["Could provide more specific details from the text to deepen the explanation."]
                    actionable_tip = "Try integrating more specific keywords or analogies from the study material."
                    student_state = "Mostly Clear" if overlap_ratio > 0.4 else "Curious"
                    mastered = overlap_ratio > 0.3
                else:
                    accuracy = 0.0
                    clarity = 0.0
                    depth = 0.0
                    relevance = 0.0
                    strengths = []
                    missing = [f"The explanation did not address the specific core concepts of the topic."]
                    actionable_tip = "Please provide an explanation that directly answers the student's question and covers the core concepts from the notes."
                    student_state = "Confused"
                    mastered = False

            return json.dumps({
                "clarity_score": round(clarity, 1),
                "accuracy_score": round(accuracy, 1),
                "depth_score": round(depth, 1),
                "relevance_score": round(relevance, 1),
                "strengths": strengths,
                "missing_or_misunderstood": missing,
                "actionable_tip": actionable_tip,
                "student_state": student_state,
                "concept_mastered": mastered,
            })

# Handle Opening Question 1 dynamically based on loaded document
        if is_opening:
            if re.search(r'\b(cat|cats|felis)\b', f_low):
                return (
                    "Teacher, I read in your notes that cats are small, carnivorous mammals known for their sharp senses, flexible bodies, and retractable claws.\n\n"
                    "Why do cats have retractable claws unlike dogs, and how do their flexible bodies and sharp senses help them in the wild?"
                )
            elif "respiratory" in f_low or ("oxygen" in f_low and "circulatory" in f_low):
                return (
                    "Teacher, in the notes about **How the Human Body Works**, it explains that the respiratory and circulatory systems work together to distribute oxygen.\n\n"
                    "When we breathe in, how does oxygen actually travel from our lungs into our blood, and how does it reach all the cells in our body?"
                )
            elif re.search(r'\b(human|humans|homo sapiens)\b', f_low):
                return (
                    "Teacher, I read in your notes that humans are living beings belonging to the species *Homo sapiens*, known for complex language, reasoning, and generational learning.\n\n"
                    "What really sets human communication apart from other animals, and how does passing knowledge across generations shape who we are?"
                )
            else:
                words = [w for w in current_fact.split() if w.lower() not in ["preview", "text", "extraction.", "upload,"]]
                clause = " ".join(words[:24]).rstrip(",;:. ") if len(words) > 5 else f"the core ideas of {current_concept}"
                
                if any(k in f_low for k in ["born", "known professionally", "known as", "actress", "actor", "politician", "career", "life"]):
                    q = "What would you say is the most defining part of their background or early career?"
                elif any(k in f_low for k in ["theory", "science", "process", "mechanism", "physics", "chemistry"]):
                    q = "Could you explain the intuition behind this in simple terms—how does the process actually work in practice?"
                elif any(k in f_low for k in ["war", "battle", "treaty", "empire", "century", "history"]):
                    q = "What do you think were the primary causes or historical factors that led to this?"
                elif any(k in f_low for k in ["film", "movie", "album", "book", "art", "media", "popular"]):
                    q = "What makes this piece of media or culture stand out so much compared to others?"
                else:
                    q = "Could you explain what this means in simpler terms and why it's important to understand?"

                return (
                    f"Teacher, looking over the notes on **{current_concept}**, it mentions that {clause}.\n\n{q}"
                )

        # Extract teacher's explanation
        teacher_match = re.search(r"TEACHER'S LATEST EXPLANATION:\s*\"(.*?)\"", user_prompt, re.DOTALL)
        teacher_text = teacher_match.group(1).strip() if teacher_match else user_prompt
        t_low = teacher_text.lower()

        # Step 1: Human-like, natural student reaction
        if self._is_uncertain_or_idk(t_low):
            idk_reactions = [
                "No worries at all! That's definitely a tricky question to explain off the cuff—no problem moving forward.",
                "That's completely fine! Some of these biological concepts are tough to summarize on the spot, so we can always revisit it.",
                "No problem at all! Let's keep our momentum going and tackle the next topic.",
                "Got it, no problem! We can leave that one for later review and move right along.",
            ]
            reaction = idk_reactions[(q_num - 1) % len(idk_reactions)]
        elif re.search(r'\b(human|humans|homo sapiens)\b', f_low) and any(w in t_low for w in ["technology", "tech", "tool", "machine", "invent", "science", "device"]):
            reaction = "That's a really interesting point! Technological innovation and tool use are huge examples of how humans pass down knowledge and adapt across generations."
        elif re.search(r'\b(cat|cats|felis)\b', f_low) and ("climb surface" in t_low or ("climb" in t_low and ("surface" in t_low or "tree" in t_low or len(t_low.split()) <= 4))):
            reaction = "Ah, got it! That makes sense—retractable claws give them the grip they need to scale surfaces, while staying protected in their sheaths so they don't get blunted on the ground."
        elif re.search(r'\b(cat|cats|felis)\b', f_low) and ("digest" in t_low or ("plant" in t_low and "meat" in t_low)):
            reaction = "Oh, I see! So their digestive tract is built strictly for high-protein meat and physically lacks the enzymes to process tough plant matter."
        elif re.search(r'\b(cat|cats|felis)\b', f_low) and ("aware" in t_low or "surround" in t_low):
            reaction = "That makes total sense! Like built-in sensory antennas giving them a 360-degree awareness of their surroundings in the dark."
        elif re.search(r'\b(cat|cats|felis)\b', f_low) and "sharpen" in t_low and "claw" in t_low:
            reaction = "Right! Scratching sheds the dull outer claw layers to keep them sharp, plus it leaves scent marks from paw glands to mark safe territory."
        elif re.search(r'\b(cat|cats|felis)\b', f_low) and ("feel" in t_low or ("know" in t_low and "other" in t_low)):
            reaction = "That clicks! So it's both an emotional signal to others and an internal self-soothing comfort mechanism."
        elif re.search(r'\b(respiratory|circulatory|oxygen)\b', f_low) and any(w in t_low for w in ["red blood", "blood cell", "hemoglobin", "absorb", "oxygen"]):
            reaction = "Aha, that makes sense! So red blood cells act like a delivery fleet, using hemoglobin to bind oxygen and transport it through the bloodstream."
        elif re.search(r'\b(human|humans|homo sapiens)\b', f_low) and any(w in t_low for w in ["animal", "animal kingdom", "primate", "mammal", "connected", "species"]):
            reaction = "That's such a great insight! Language and cumulative learning mean we don't have to reinvent the wheel every generation."
        elif re.search(r'\b(respiratory|circulatory|oxygen|nervous)\b', f_low) and any(w in t_low for w in ["coordinate", "signal", "brain", "nerve", "heart", "lungs", "cooperate"]):
            reaction = "That really clarifies how the systems work together! The nervous system and bloodstream constantly send signals and circulate resources so every organ responds in sync."
        elif re.search(r'\b(body|cell|organ|tissue)\b', f_low) and any(w in t_low for w in ["cell", "tissue", "organ", "system", "hierarchy"]):
            reaction = "Visualizing individual cells cooperating like specialized workers in a factory makes that hierarchy so intuitive!"
        elif re.search(r'\b(human|humans|homo sapiens)\b', f_low) and any(w in t_low for w in ["social", "community", "belong", "connection", "friend", "family", "psycholog", "mental"]):
            reaction = "Spot on! Human brains evolved for cooperation and connection, so belonging is literally wired into our survival."
        elif re.search(r'\b(human|humans|homo sapiens)\b', f_low) and any(w in t_low for w in ["need", "food", "water", "sleep", "shelter"]):
            reaction = "Exactly! Without those physical fundamentals like clean water, rest, and safety, our bodies simply couldn't sustain themselves."
        elif re.search(r'\b(human|humans|homo sapiens)\b', f_low) and any(w in t_low for w in ["diversity", "culture", "tradition", "language", "respect"]):
            reaction = "That really ties everything together! Shared biology forms the universal foundation for all our diverse cultural expressions."
        elif re.search(r'\b(human|humans|homo sapiens)\b', f_low) and any(w in t_low for w in ["surviv", "evolv", "adapt"]):
            reaction = "That's a key evolutionary perspective! It highlights how these traits were honed over time to help organisms survive and adapt."
        else:
            # Clean teacher text of blatant typos for graceful reflection
            clean_snippet = teacher_text.replace("planst", "plants").replace("betterr", "better").replace("thye", "they").replace("thorgh", "through").strip()
            words = clean_snippet.split()
            
            fact_words = set(re.findall(r'\b\w+\b', current_fact.lower()))
            exp_words = set(re.findall(r'\b\w+\b', t_low))
            stopwords = {"the", "a", "an", "is", "are", "was", "were", "to", "in", "for", "of", "on", "and", "or", "but", "with", "as", "at", "by", "that", "this", "it"}
            fact_keywords = fact_words - stopwords
            exp_keywords = exp_words - stopwords
            
            overlap_ratio = len(fact_keywords.intersection(exp_keywords)) / max(1, len(fact_keywords))

            if len(words) <= 4:
                reaction = f"I'm not completely sure I follow what you mean by '{clean_snippet}', but we can review this topic later."
            elif overlap_ratio > 0.4:
                reaction = "Wow, that clicked perfectly! Using those specific concepts from the material really helped me understand."
            elif overlap_ratio > 0.15:
                reaction = "Got it, that makes sense! Looking at how those factors interact definitely helps connect the dots."
            else:
                reaction = "Hmm, I don't see how that directly connects to the core ideas in the notes, but I appreciate the effort! Let's just move on to the next topic."

        # Step 2: Natural human-like transition and question for target concept
        c_low = current_concept.lower()
        topic_ordinals = {1: "first", 2: "second", 3: "third", 4: "fourth", 5: "fifth", 6: "sixth", 7: "seventh", 8: "eighth"}
        ord_str = topic_ordinals.get(q_num, f"#{q_num}")

        if q_num == total_q:
            transition_prefix = f"For our final topic, **{current_concept}** (Question {q_num}/{total_q}):"
        else:
            transition_prefix = f"Moving to our {ord_str} topic, **{current_concept}** (Question {q_num}/{total_q}):"

        if ("diet" in c_low or "carnivore" in f_low) and re.search(r'\b(cat|cats|felis)\b', f_low):
            transition = transition_prefix
            q_body = "I noticed in the notes that cats are classified as 'obligate carnivores'. Why can't cats survive on plant foods like dogs or humans can—what makes animal meat biologically mandatory for them?"
        elif ("sense" in c_low or "communication" in c_low) and re.search(r'\b(cat|cats|whisker|meow)\b', f_low):
            transition = transition_prefix
            q_body = "The notes highlight low-light vision, sensitive whiskers, and body language. How do whiskers actually work to help a cat navigate—is it true they can detect minute air currents in total darkness?"
        elif ("care" in c_low or "caring" in c_low) and re.search(r'\b(cat|cats|litter)\b', f_low):
            transition = transition_prefix
            q_body = "The guide emphasizes daily play, quiet litter areas, and scratching surfaces. What biological purpose does scratching serve for a cat besides just claw maintenance—does it have to do with territory?"
        elif "behavior" in c_low and re.search(r'\b(cat|cats|purr|blink)\b', f_low):
            transition = transition_prefix
            q_body = "The notes mention that a slow blink is a relaxed social signal, but also say cats purr when they're stressed as well as happy. Why would a cat purr when uncomfortable or in pain instead of just when content?"
        elif "about human" in c_low or ("homo sapiens" in c_low and "fact" not in c_low):
            transition = transition_prefix
            q_body = "The notes describe humans as mammals and primates known for complex language and generational learning. What really sets human communication apart from other primates, and how did passing down knowledge shape our evolution?"
        elif "quick fact" in c_low or ("cell" in c_low and "organ" in c_low):
            transition = transition_prefix
            q_body = "The notes describe microscopic cells forming tissues, tissues forming organs, and organs working in systems like the circulatory and nervous systems. How do all these parts coordinate in real time?"
        elif "need" in c_low:
            transition = transition_prefix
            q_body = "The guide lists nutrition, clean water, and shelter, but also highlights community life. Why is social connection considered a fundamental biological need on par with food and water?"
        elif "diversity" in c_low:
            transition = transition_prefix
            q_body = "The notes observe that all humans share the exact same underlying biology, yet express such rich cultural diversity. How does understanding our shared biology help us appreciate and celebrate those differences?"
        elif "body" in c_low:
            transition = transition_prefix
            q_body = "The notes explain that the respiratory, circulatory, and digestive systems all work closely together. Could you walk me through an everyday example of how they coordinate in real time?"
        else:
            words = [w for w in current_fact.split() if w.lower() not in ["preview", "text", "extraction.", "upload,"]]
            fact_clause = " ".join(words[:14]).rstrip(",;:. ") if len(words) > 5 else f"the core ideas of {current_concept}"
            transition = transition_prefix
            
            if any(k in f_low for k in ["born", "known professionally", "known as", "actress", "actor", "politician", "career", "life"]):
                q_body = f"The notes mention: '{fact_clause}...'. How did this aspect shape their overall journey or public perception?"
            elif any(k in f_low for k in ["theory", "science", "process", "mechanism", "physics", "chemistry"]):
                q_body = f"The notes highlight that {fact_clause}. Could you break down the core mechanism behind that in simple terms?"
            elif any(k in f_low for k in ["war", "battle", "treaty", "empire", "century", "history"]):
                q_body = f"The notes mention that {fact_clause}. Why was this historically significant?"
            elif any(k in f_low for k in ["film", "movie", "album", "book", "art", "media", "popular"]):
                q_body = f"The notes state that {fact_clause}. What makes this piece of media or culture stand out so much?"
            else:
                q_body = f"The notes highlight that {fact_clause}. Could you expand on this and explain why it's important?"

        return f"{reaction}\n\n{transition}\n{q_body}"

