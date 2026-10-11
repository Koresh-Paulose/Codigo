from sqlalchemy import func
from models import Turn

WEIGHTS = {"coverage": 25, "accuracy": 30, "clarity": 15, "flaw": 15, "independence": 15}
HINT_POINTS = {0: 100, 1: 85, 2: 70, 3: 50, 4: 20}

def independence_score(db, session_id, concept_ids):
    rows = (db.query(Turn.concept_id, func.max(Turn.hint_level))
              .filter(Turn.session_id == session_id, Turn.is_exam == False,
                      Turn.concept_id.in_(concept_ids))
              .group_by(Turn.concept_id).all())
    level = {cid: lvl or 0 for cid, lvl in rows}
    pts = [HINT_POINTS[min(4, level.get(cid, 0))] for cid in concept_ids]
    return round(sum(pts) / len(pts)) if pts else 100

def build_parts(db, session_id, concepts, evaluation):
    ids = [c.id for c in concepts]
    pq = list(evaluation["per_question"].values())
    n = max(1, len(pq))
    flaw = evaluation["flaw_caught"]
    return {
        "coverage": round(100 * len(set(evaluation["covered"])) / max(1, len(ids))),
        "accuracy": round(100 * sum(p["accuracy"] for p in pq) / (5 * n)),
        "clarity": round(100 * sum(p["clarity"] for p in pq) / (5 * n)),
        "flaw": None if flaw is None else (100 if flaw else 0),
        "independence": independence_score(db, session_id, ids),
    }

def combine(parts):
    w = {k: v for k, v in WEIGHTS.items() if parts.get(k) is not None}
    return round(sum(parts[k] * w[k] for k in w) / sum(w.values()))