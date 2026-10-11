import sys
import os
import argparse
from pathlib import Path

# Ensure UTF-8 output encoding if supported by terminal
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from .session import StudentSession
from .config import get_active_llm_mode
from .document_reader import DocumentReader

# ANSI colors for terminal
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
RESET = "\033[0m"
DIM = "\033[2m"

def print_banner():
    banner = f"""
{CYAN}+==========================================================================+
|               PROTEGE: AI STUDENT TEACHING TERMINAL                      |
|      Feynman Learning System * Multi-Tier LLM * Active Study Series       |
+==========================================================================+{RESET}
"""
    print(banner)

def run_demo(session: StudentSession):
    """Automated demonstration mode for testing questions."""
    print(f"\n{YELLOW}[Running Automated Demo Mode - {session.total_questions} Topical Questions]{RESET}\n")
    first_q = session.start()
    print(f"{CYAN}{BOLD}[AI Student - {session.persona.name}] (Question 1/{session.total_questions} * {session.current_concept}){RESET}")
    print(f"{first_q}\n")

    demo_explanations = [
        "Cats have retractable claws to keep them razor sharp for hunting and climbing, while flexible bodies give them incredible balance and agility.",
        "They are obligate carnivores with the scientific name Felis catus, meaning their bodies cannot synthesize certain vital amino acids like taurine without meat.",
        "Whiskers are rich in nerve endings and act like radar, detecting minute air currents so cats can measure gaps and navigate total darkness.",
        "Scratching surfaces allow cats to shed outer nail sheaths and deposit scent from paw glands to mark their safe territory.",
        "A slow blink is an affectionate social smile, while purring can be contentment or self-soothing when in pain.",
    ]

    for explanation in demo_explanations[:session.total_questions]:
        print(f"{BOLD}[Teacher (Simulated)]{RESET} {explanation}\n")
        result = session.step(explanation)

        if result["is_series_complete"]:
            print(f"{CYAN}{BOLD}[AI Student - {session.persona.name}]{RESET}")
            print(f"{result['student_reply']}\n")
            break
        else:
            q_num = result.get("question_number", 2)
            topic = result.get("next_concept", "Topic")
            print(f"{CYAN}{BOLD}[AI Student - {session.persona.name}] (Question {q_num}/{session.total_questions} * {topic}){RESET}")
            print(f"{result['student_reply']}\n")

    print(f"{GREEN}[All {session.total_questions} Questions Completed - Final Performance Report]{RESET}")
    print(session.get_final_report())

def main():
    parser = argparse.ArgumentParser(description="Protege AI Student Teaching Terminal")
    parser.add_argument("--file", "-f", type=str, help="Path to document file (PDF, Markdown, TXT)")
    parser.add_argument("--topic", "-t", type=str, help="Direct topic to study without a document (e.g. 'Photosynthesis')")
    parser.add_argument("--questions", "-q", type=int, default=None, help="Number of questions in study series (default: 5)")
    parser.add_argument("--sample", action="store_true", help="Load built-in sample study notes")
    parser.add_argument("--demo", action="store_true", help="Run automated end-to-end demo test")
    parser.add_argument("--persona", type=str, default="novice", choices=["novice", "peer", "pragmatic"], help="Student persona type")
    args = parser.parse_args()

    print_banner()

    sample_file_path = Path(__file__).resolve().parent / "sample_notes.md"
    session = None

    if args.topic:
        print(f"\n{CYAN}[AI Researcher] Autonomously researching topic: '{args.topic}'...{RESET}")
        session = StudentSession(topic=args.topic, persona_type=args.persona)
    elif args.sample:
        session = StudentSession(file_path=str(sample_file_path), persona_type=args.persona)
    elif args.file:
        target_file = DocumentReader.sanitize_path(args.file)
        session = StudentSession(file_path=target_file, persona_type=args.persona)
    elif args.demo:
        session = StudentSession(file_path=str(sample_file_path), persona_type=args.persona)
    else:
        print(f"Active LLM Mode: {BOLD}{get_active_llm_mode()}{RESET}")
        print("Tip: Paste a file path (.pdf, .md, .txt), OR type any topic directly (e.g. 'Photosynthesis', 'Quantum Computing'), or press [Enter] for sample notes.")
        user_input = input(f"\nEnter file path OR topic: ").strip()
        if not user_input:
            session = StudentSession(file_path=str(sample_file_path), persona_type=args.persona)
        elif Path(DocumentReader.sanitize_path(user_input)).exists():
            clean_file = DocumentReader.sanitize_path(user_input)
            session = StudentSession(file_path=clean_file, persona_type=args.persona)
        else:
            print(f"\n{CYAN}[AI Researcher] Researching topic: '{user_input}'...{RESET}")
            session = StudentSession(topic=user_input, persona_type=args.persona)

    doc = session.doc
    if doc.file_name.startswith("Topic:"):
        print(f"\n{GREEN}[OK] Curriculum Prepared:{RESET} {BOLD}{doc.file_name}{RESET} ({doc.word_count} words researched)")
    else:
        print(f"\n{GREEN}[OK] Document Loaded:{RESET} {BOLD}{doc.file_name}{RESET} ({doc.word_count} words)")

    # Prompt user for how many questions to ask before beginning questioning
    num_questions = args.questions if hasattr(args, "questions") and args.questions else None
    if num_questions is None and not args.demo:
        try:
            q_input = input(f"How many questions would you like to be asked? [default: 5]: ").strip()
            if q_input:
                num_questions = max(1, int(q_input))
            else:
                num_questions = 5
        except (ValueError, KeyboardInterrupt, EOFError):
            num_questions = 5
    elif num_questions is None:
        num_questions = 5

    session.set_total_questions(num_questions)

    print(f"\n{BOLD}Topics in this study series ({session.total_questions} questions total):{RESET}")
    for i, c in enumerate(doc.concepts[:session.total_questions], 1):
        print(f"  {i}. {c}")

    print(f"\n{DIM}{session.persona.name} will ask {session.total_questions} questions on these topics. Answer naturally.{RESET}")
    print(f"{DIM}Commands: /done (finishes early & prints report) | /help{RESET}\n")

    if args.demo:
        run_demo(session)
        return

    # Start interactive chat session with Question 1
    initial_question = session.start()
    print(f"{initial_question}\n")

    while True:
        try:
            user_text = input(f"{BOLD}[Teacher] You:{RESET} ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting session...")
            break

        if not user_text:
            continue

        cmd = user_text.lower()
        if cmd in ["/done", "/finish", "/quit", "/exit", "/stop", "quit", "exit", "done", "stop", "q"]:
            print(f"\n{GREEN}[Study Session Concluded Early - Performance Report for Completed Questions ({session.metrics.total_turns}/{session.total_questions})]{RESET}")
            print(session.get_final_report())

            if session.metrics.overall_teaching_score < 50:
                print(f"\n{YELLOW}[Notice] Your overall score was {session.metrics.overall_teaching_score:.1f}% (Below 50%).{RESET}")
                try:
                    retest_choice = input(f"{BOLD}Would you like to retest on this material? (Type '/retest' to try again, or Enter to exit): {RESET}").strip().lower()
                    if retest_choice in ["/retest", "retest", "y", "yes"]:
                        print(f"\n{GREEN}[Restarting Study Session - {session.total_questions} Question Series]{RESET}\n")
                        new_q = session.retest()
                        print(f"{new_q}\n")
                        continue
                except (KeyboardInterrupt, EOFError):
                    pass
            break

        elif cmd in ["/retest", "retest"]:
            print(f"\n{GREEN}[Restarting Study Session - {session.total_questions} Question Series]{RESET}\n")
            new_q = session.retest()
            print(f"{new_q}\n")
            continue

        elif cmd in ["/metrics", "/summary", "/report"]:
            print(session.get_final_report())
            continue

        elif cmd == "/concepts":
            print(f"\n{BOLD}Mastered Topics:{RESET} {', '.join(session.metrics.mastered_concepts) or 'None yet'}")
            print(f"{BOLD}Pending Topics :{RESET} {', '.join(session.metrics.pending_concepts) or 'All done!'}\n")
            continue

        elif cmd == "/help":
            print("\nAvailable commands:")
            print("  /quit or /done - Conclude study session at any point and view your performance report")
            print("  /retest        - Restart the study series from the beginning")
            print("  /report        - Preview your current performance report")
            print("  /concepts      - View list of covered vs remaining topics\n")
            continue

        # Process teacher explanation
        result = session.step(user_text)

        if result["is_series_complete"]:
            print(f"\n{CYAN}{BOLD}[AI Student - {session.persona.name}]{RESET}")
            print(f"{result['student_reply']}\n")

            if session.metrics.overall_teaching_score < 50:
                print(f"\n{YELLOW}[Notice] Your overall score was {session.metrics.overall_teaching_score:.1f}% (Below 50%).{RESET}")
                try:
                    retest_choice = input(f"{BOLD}Would you like to retest on this material? (Type '/retest' to try again, or Enter to exit): {RESET}").strip().lower()
                    if retest_choice in ["/retest", "retest", "y", "yes"]:
                        print(f"\n{GREEN}[Restarting Study Session - {session.total_questions} Question Series]{RESET}\n")
                        new_q = session.retest()
                        print(f"{new_q}\n")
                        continue
                except (KeyboardInterrupt, EOFError):
                    pass
            break
        else:
            print(f"\n{result['student_reply']}\n")

if __name__ == "__main__":
    main()
