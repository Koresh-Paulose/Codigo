from db import SessionLocal, Base, engine
import models
from models import StudySession, Concept, Turn

Base.metadata.create_all(bind=engine)

with SessionLocal() as db:
    s = StudySession(
        flaw_claim="Binary search works on any array, sorted or not.",
        flaw_truth="Binary search only works correctly on a sorted array.",
    )
    db.add(s)
    db.flush()

    data = [
        ("Binary search", "Repeatedly halves a sorted array by comparing the target with the middle element."),
        ("Time complexity of binary search", "O(log n), because the search space halves every step."),
        ("Sorted-input requirement", "The array must be sorted, otherwise discarding half is invalid."),
        ("Linear search", "Checks elements one by one; O(n); works on unsorted data."),
    ]
    concepts = []
    for name, summary in data:
        c = Concept(session_id=s.id, name=name, summary=summary)
        db.add(c)
        concepts.append(c)
    db.flush()

    chat = [
        ("student", "I think binary search works on any array, right?", None, 0),
        ("user", "No, the array has to be sorted, otherwise halving makes no sense.", concepts[2].id, 0),
        ("student", "Why is it fast?", None, 0),
        ("user", "It cuts the remaining items in half each step so it's about log n.", concepts[1].id, 1),
    ]
    for role, text, cid, hint in chat:
        db.add(Turn(session_id=s.id, role=role, content=text, concept_id=cid, hint_level=hint))
    db.commit()
    print("Seeded session id:", s.id)