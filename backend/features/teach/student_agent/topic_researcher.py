import json
import re
from typing import Optional, Dict, Any, List
from .document_reader import DocumentKnowledge, TopicFact
from .llm_client import LLMClient

# Built-in knowledge bases for popular topics when running offline / local fallback
PRESET_TOPIC_KNOWLEDGE: Dict[str, Dict[str, Any]] = {
    "photosynthesis": {
        "title": "Photosynthesis",
        "overview": "Photosynthesis is the biochemical process by which photoautotrophs (plants, algae, and cyanobacteria) convert light energy into chemical energy stored in glucose molecules. It consists of light-dependent reactions in the thylakoid membranes and the Calvin cycle (light-independent reactions) in the chloroplast stroma.",
        "subtopics": [
            {
                "title": "Chloroplasts & Chlorophyll",
                "fact": "Chloroplasts are specialized plant organelles containing chlorophyll pigments that selectively absorb blue and red wavelengths of light while reflecting green light.",
                "sample_question": "Why do plants reflect green light instead of absorbing it, and how does chlorophyll capture photon energy from sunlight?"
            },
            {
                "title": "Light-Dependent Reactions",
                "fact": "Occurring in the thylakoid membrane, light energy splits water molecules (photolysis) to release oxygen gas and generate high-energy electron carriers (ATP and NADPH).",
                "sample_question": "When water molecules split in the thylakoid membrane, where does the oxygen go, and how do ATP and NADPH get produced?"
            },
            {
                "title": "The Calvin Cycle (Dark Reactions)",
                "fact": "In the stroma, the enzyme RuBisCO fixes carbon dioxide (CO2) from the air with RuBP to synthesize 3-carbon sugars (G3P), which combine to form glucose.",
                "sample_question": "How does the Calvin cycle turn atmospheric carbon dioxide into actual sugar molecules without needing direct sunlight?"
            },
            {
                "title": "Environmental Limiting Factors",
                "fact": "The rate of photosynthesis is regulated by three main limiting factors: light intensity, atmospheric CO2 concentration, and temperature.",
                "sample_question": "Why does increasing temperature beyond a certain point decrease the rate of photosynthesis instead of accelerating it?"
            },
            {
                "title": "Ecological Significance & Oxygen Cycle",
                "fact": "Photosynthesis forms the foundation of Earth's food webs as primary production and generated the oxygen-rich atmosphere that sustains aerobic cellular respiration.",
                "sample_question": "How did early photosynthetic organisms alter Earth's prehistoric atmosphere, and how does that link to aerobic animal life today?"
            }
        ]
    },
    "quantum computing": {
        "title": "Quantum Computing",
        "overview": "Quantum computing leverages the fundamental principles of quantum mechanics—namely superposition, entanglement, and quantum interference—to solve complex computational problems exponentially faster than classical computers.",
        "subtopics": [
            {
                "title": "Qubits vs Classical Bits",
                "fact": "Unlike classical bits that are strictly 0 or 1, quantum bits (qubits) can exist in a linear superposition of both states simultaneously until measured.",
                "sample_question": "How can a qubit exist as both 0 and 1 at the same time, and what happens to that state the exact moment you observe or measure it?"
            },
            {
                "title": "Quantum Superposition",
                "fact": "Superposition allows a quantum system of n qubits to represent 2^n states simultaneously, creating an exponentially large computational space.",
                "sample_question": "Why does adding qubits scale a quantum computer's potential computing power exponentially rather than linearly?"
            },
            {
                "title": "Quantum Entanglement",
                "fact": "Entangled qubits exhibit correlated quantum states such that the state of one qubit instantly dictates the state of another, regardless of physical separation.",
                "sample_question": "How does quantum entanglement allow two qubits to be coordinated without transmitting classical data between them?"
            },
            {
                "title": "Quantum Decoherence & Noise",
                "fact": "Qubits are fragile and easily disturbed by thermal fluctuations, electromagnetic radiation, and environmental noise, causing decoherence and computational errors.",
                "sample_question": "What causes quantum decoherence, and why do current quantum processors require cryogenic cooling near absolute zero?"
            },
            {
                "title": "Quantum Algorithms & Applications",
                "fact": "Algorithms like Shor's algorithm for prime factorization and Grover's algorithm for database search provide substantial speedups over classical algorithms in cryptography and material science.",
                "sample_question": "How does Shor's algorithm threaten classical RSA encryption, and what types of problems is quantum computing best suited to solve?"
            }
        ]
    },
    "black holes": {
        "title": "Black Holes",
        "overview": "Black holes are regions of spacetime where gravitational forces are so intense that nothing—not even light—has sufficient velocity to escape. Predicted by Einstein's General Theory of Relativity, they represent the ultimate gravitational collapse of massive stars.",
        "subtopics": [
            {
                "title": "Gravitational Collapse & Formation",
                "fact": "Stellar black holes form when a massive star exhausts its nuclear fuel and undergoes runaway gravitational collapse, overcoming electron and neutron degeneracy pressures.",
                "sample_question": "What prevents a dying massive star from stabilizing, causing it to collapse all the way into a black hole?"
            },
            {
                "title": "The Event Horizon & Schwarzschild Radius",
                "fact": "The event horizon marks the boundary of no return, defined by the Schwarzschild radius, where escape velocity equals the speed of light.",
                "sample_question": "If you crossed the event horizon of a black hole, why could light never escape back out to the outside universe?"
            },
            {
                "title": "Gravitational Singularity",
                "fact": "At the center of a non-rotating black hole lies a singularity, a point of infinite mathematical density where known laws of classical physics and general relativity break down.",
                "sample_question": "What is a gravitational singularity, and why do physicists say our current laws of physics break down there?"
            },
            {
                "title": "Hawking Radiation & Black Hole Evaporation",
                "fact": "Stephen Hawking showed that quantum vacuum fluctuations near the event horizon cause virtual particle-antiparticle pairs to separate, causing black holes to slowly radiate energy and lose mass.",
                "sample_question": "How can a black hole emit Hawking radiation and lose mass if nothing is supposed to escape its gravity?"
            },
            {
                "title": "Spacetime Warping & Gravitational Lensing",
                "fact": "Massive black holes dramatically bend spacetime, causing gravitational time dilation (time slows down near the horizon) and lensing light from distant background stars.",
                "sample_question": "How does intense gravity slow down time for an observer near a black hole compared to someone watching from deep space?"
            }
        ]
    },
    "neural networks": {
        "title": "Neural Networks & Deep Learning",
        "overview": "Artificial neural networks are computational models loosely inspired by biological brains, composed of interconnected layers of artificial neurons that learn representations from training data via backpropagation and gradient descent.",
        "subtopics": [
            {
                "title": "Artificial Neurons & Activations",
                "fact": "Each artificial neuron computes a weighted sum of its inputs, adds a bias term, and applies a non-linear activation function (like ReLU or Sigmoid) to enable modeling non-linear patterns.",
                "sample_question": "Why do neural networks require non-linear activation functions instead of just adding up weighted numbers?"
            },
            {
                "title": "Forward Propagation & Loss Functions",
                "fact": "Inputs pass layer-by-layer through the network to generate predictions, which are compared against target labels using a loss function (like Cross-Entropy or Mean Squared Error).",
                "sample_question": "How does a loss function quantify how well or poorly a deep neural network is currently performing?"
            },
            {
                "title": "Backpropagation & Gradient Descent",
                "fact": "Backpropagation applies the calculus chain rule to compute gradients of the loss with respect to all network weights, allowing optimizers (like Adam or SGD) to iteratively minimize error.",
                "sample_question": "Can you explain how backpropagation uses the chain rule to figure out which weights in early layers need adjusting?"
            },
            {
                "title": "Overfitting & Regularization",
                "fact": "Networks can memorize training data rather than generalizing, mitigated by techniques like dropout, weight decay (L2 regularization), data augmentation, and early stopping.",
                "sample_question": "What is the difference between a model generalizing versus simply overfitting and memorizing training examples?"
            },
            {
                "title": "Deep Architectures (CNNs & Transformers)",
                "fact": "Modern deep learning uses specialized inductive biases: Convolutional Neural Networks (CNNs) for spatial imagery, and Transformers with self-attention for sequential and linguistic reasoning.",
                "sample_question": "Why are Transformers and attention mechanisms better suited for language understanding than older recurrent networks?"
            }
        ]
    },
    "world war ii": {
        "title": "World War II",
        "overview": "World War II (1939–1945) was a global conflict between the Allied Powers and the Axis Powers, fundamentally reshaping geopolitical boundaries, human rights institutions, and military technology.",
        "subtopics": [
            {
                "title": "Origins & Rise of Totalitarianism",
                "fact": "The destabilizing Treaty of Versailles, the Great Depression, and unchecked militarism facilitated the rise of fascist regimes in Germany, Italy, and Japan.",
                "sample_question": "How did the economic fallout of the 1930s and the Treaty of Versailles pave the way for the rise of totalitarian regimes?"
            },
            {
                "title": "Blitzkrieg & European Theaters",
                "fact": "Germany's fast, coordinated mechanized tactics (Blitzkrieg) overwhelmed mainland Europe before stalling in the Battle of Britain and the Eastern Front.",
                "sample_question": "What made the Blitzkrieg strategy so devastatingly effective in 1939-1940 compared to World War I trench warfare?"
            },
            {
                "title": "The Eastern Front & Battle of Stalingrad",
                "fact": "The brutal collision between the Soviet Union and Nazi Germany along the Eastern Front, climaxing at Stalingrad, became the decisive turning point of the European conflict.",
                "sample_question": "Why is the Battle of Stalingrad considered the central military turning point of World War II in Europe?"
            },
            {
                "title": "The Pacific Theater & Island Hopping",
                "fact": "Following the attack on Pearl Harbor, Allied naval forces employed an 'island-hopping' campaign across Pacific archipelagos toward the Japanese mainland.",
                "sample_question": "How did the Allied island-hopping strategy overcome vast oceanic distances in the Pacific theater?"
            },
            {
                "title": "Aftermath & Postwar World Order",
                "fact": "The conclusion of the war witnessed the devastation of the Holocaust, the dawn of the nuclear era, the partition of Europe into the Cold War, and the founding of the United Nations.",
                "sample_question": "How did the end of World War II immediately set the stage for the Cold War and the creation of the United Nations?"
            }
        ]
    }
}

class TopicResearcher:
    """Autonomously researches topics and generates comprehensive study curricula."""

    @classmethod
    def research_topic(cls, topic_query: str, llm_client: Optional[LLMClient] = None) -> DocumentKnowledge:
        """Researches a topic query via LLM or built-in intelligent topic synthesis."""
        clean_topic = topic_query.strip().strip("'\"")
        if not clean_topic:
            clean_topic = "General Knowledge"

        t_low = clean_topic.lower()

        # 1. Try Gemini / Groq live research if client is active with keys
        if llm_client and (llm_client.gemini_api_key or llm_client.groq_api_key):
            try:
                knowledge = cls._research_via_llm(clean_topic, llm_client)
                if knowledge:
                    return knowledge
            except Exception as e:
                print(f"[TopicResearcher] Live LLM research failed ({e}). Using intelligent curriculum synthesis...")

        # 2. Check preset high-fidelity knowledge bases
        for key, preset in PRESET_TOPIC_KNOWLEDGE.items():
            if key in t_low or t_low in key:
                return cls._build_knowledge_from_dict(clean_topic, preset)

        # 3. Dynamic intelligent curriculum synthesis for ANY arbitrary topic
        return cls._synthesize_custom_topic(clean_topic)

    @classmethod
    def _research_via_llm(cls, topic: str, client: LLMClient) -> Optional[DocumentKnowledge]:
        system_prompt = (
            "You are an expert pedagogical curriculum researcher. "
            "A user is going to practice the Feynman Technique by teaching an AI student on a chosen topic. "
            "Your task is to outline 5 fundamental, distinct subtopics that the teacher must explain to demonstrate true mastery.\n"
            "Return STRICT valid JSON only without markdown codeblocks:\n"
            "{\n"
            '  "title": "<Clean Topic Title>",\n'
            '  "overview": "<2-3 sentence clear conceptual summary>",\n'
            '  "subtopics": [\n'
            '    {\n'
            '      "title": "<Subtopic Name>",\n'
            '      "fact": "<2-3 sentence rigorous explanation of how and why it works>",\n'
            '      "sample_question": "<A curious student question probing the mechanism>"\n'
            "    }\n"
            "  ]\n"
            "}"
        )
        user_prompt = f"Please research and create the 5 core learning topics for: '{topic}'"

        response = client.generate(system_prompt=system_prompt, user_prompt=user_prompt, temperature=0.4)
        if not response:
            return None

        # Clean JSON
        json_match = re.search(r"\{.*\}", response, re.DOTALL)
        if not json_match:
            return None

        data = json.loads(json_match.group(0))
        return cls._build_knowledge_from_dict(topic, data)

    @classmethod
    def _build_knowledge_from_dict(cls, topic: str, data: Dict[str, Any]) -> DocumentKnowledge:
        title = data.get("title", topic)
        overview = data.get("overview", f"Educational curriculum covering core principles of {topic}.")
        subtopics = data.get("subtopics", [])

        topic_facts: List[TopicFact] = []
        concepts: List[str] = []

        full_content_lines = [f"# Topic: {title}", "", overview, "", "## Key Curriculum Concepts:"]

        for st in subtopics:
            st_title = st.get("title", "Concept")
            st_fact = st.get("fact", "Key foundational principles.")
            st_q = st.get("sample_question", f"Could you explain how {st_title} works in practice?")

            concepts.append(st_title)
            topic_facts.append(TopicFact(title=st_title, fact=st_fact, sample_question=st_q))
            full_content_lines.append(f"### {st_title}\n{st_fact}\n")

        full_content = "\n".join(full_content_lines)
        word_count = len(full_content.split())

        return DocumentKnowledge(
            file_name=f"Topic: {title}",
            file_path=None,
            content=full_content,
            summary=overview,
            concepts=concepts,
            topic_facts=topic_facts,
            word_count=word_count,
        )

    @classmethod
    def _synthesize_custom_topic(cls, topic: str) -> DocumentKnowledge:
        """Synthesizes a structured curriculum. Tries Wikipedia first as a fallback, then uses generic templates."""
        import urllib.request
        import urllib.parse
        import re

        wiki_extract = ""
        try:
            # Attempt to grab a real summary from Wikipedia
            url = f"https://en.wikipedia.org/w/api.php?action=query&generator=search&gsrsearch={urllib.parse.quote(topic)}&gsrlimit=1&prop=extracts&exintro&explaintext&format=json"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) ProtegeAI/1.0'})
            res = urllib.request.urlopen(req, timeout=3)
            data = json.loads(res.read().decode('utf-8'))
            if 'query' in data and 'pages' in data['query']:
                pages = data['query']['pages']
                wiki_extract = list(pages.values())[0].get('extract', '')
        except Exception as e:
            print(f"[TopicResearcher] Wikipedia fallback failed: {e}")

        # If we got a decent chunk of text, split into sentences
        if len(wiki_extract) > 100:
            # Clean up citations and newlines
            wiki_extract = re.sub(r'\[.*?\]', '', wiki_extract)
            wiki_extract = wiki_extract.replace('\n', ' ')
            
            # Simple sentence splitting
            sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', wiki_extract) if len(s.strip()) > 20]
            
            if len(sentences) >= 3:
                pillars = []
                stopwords = {'the', 'and', 'a', 'to', 'of', 'in', 'is', 'that', 'it', 'on', 'this', 'for', 'but', 'with', 'are', 'have', 'be', 'at', 'or', 'as', 'was', 'so', 'if', 'out', 'not', 'by', 'from', 'an', 'they', 'which', 'their', 'has', 'its', 'can', 'also', 'were', 'been', 'into', 'who', 'than', 'more', 'some'}
                topic_low = topic.lower()
                
                for i in range(5):
                    if i < len(sentences):
                        fact = sentences[i]
                    else:
                        fact = sentences[-1] # fallback to repeating last if too few sentences
                        
                    if i == 0:
                        title = f"Introduction to {topic.title()}"
                    elif i == 4:
                        title = f"Significance & Impact"
                    else:
                        # Extract capitalized words (excluding first word of sentence)
                        caps = re.findall(r'(?<=\s)[A-Z][a-z]+', fact)
                        caps = [c for c in caps if c.lower() not in topic_low and len(c) > 2]
                        caps = list(dict.fromkeys(caps))
                        
                        if len(caps) >= 2:
                            title = f"Context: {caps[0]} & {caps[1]}"
                        elif len(caps) == 1:
                            title = f"The Role of {caps[0]}"
                        else:
                            # Use longest meaningful words
                            words = re.findall(r'\b[a-zA-Z]+\b', fact.lower())
                            words = [w for w in words if w not in stopwords and w not in topic_low and len(w) > 4]
                            words = sorted(list(set(words)), key=len, reverse=True)
                            
                            if len(words) >= 2:
                                prefixes = ["Understanding", "Focus on", "Aspects of"]
                                title = f"{prefixes[i % len(prefixes)]} {words[0].title()} & {words[1].title()}"
                            elif len(words) == 1:
                                title = f"Exploring {words[0].title()}"
                            else:
                                title = f"Key Characteristics"
                        
                    q = f"The notes mention: '{fact}'. Could you explain what this means in simpler terms and why it's important?"
                    pillars.append((title, fact, q))
                
                data = {
                    "title": topic.title(),
                    "overview": f"A structured study series based on fundamental facts about {topic}.",
                    "subtopics": [{"title": title, "fact": fact, "sample_question": q} for title, fact, q in pillars]
                }
                return cls._build_knowledge_from_dict(topic, data)

        # Fallback to generic template if Wikipedia fails or has too little text
        pillars = [
            (
                f"Core Principles & Definition of {topic}",
                f"{topic} encompasses fundamental concepts, operational definitions, and essential foundational principles that govern how the field or phenomenon is understood.",
                f"What is the core intuition behind {topic}, and how would you explain it in simple terms to someone encountering it for the first time?"
            ),
            (
                f"Underlying Mechanisms & How {topic} Works",
                f"The internal mechanics of {topic} rely on interconnected processes, functional components, and cause-and-effect relationships that produce observable results.",
                f"How does {topic} actually work in practice—what are the step-by-step mechanisms driving it?"
            ),
            (
                f"Real-World Applications & Examples of {topic}",
                f"Practical applications of {topic} demonstrate how its theories are implemented in industry, nature, technology, or historical human scenarios.",
                f"Could you give me a vivid everyday example or real-world case study showing {topic} in action?"
            ),
            (
                f"Nuances, Edge Cases & Challenges in {topic}",
                f"Mastery of {topic} requires understanding common misconceptions, operational limitations, boundary constraints, and unresolved questions.",
                f"What are the biggest misconceptions or difficult edge cases people encounter when studying {topic}?"
            ),
            (
                f"Significance & Future Impact of {topic}",
                f"{topic} has broad systemic implications, connecting with adjacent domains and driving future innovations, debates, and advancements.",
                f"Why does {topic} matter so much in the bigger picture, and where is it heading in the future?"
            ),
        ]

        data = {
            "title": topic.title(),
            "overview": f"A structured Feynman learning series designed to explore and master {topic} through intuitive teaching.",
            "subtopics": [{"title": title, "fact": fact, "sample_question": q} for title, fact, q in pillars]
        }

        return cls._build_knowledge_from_dict(topic, data)
