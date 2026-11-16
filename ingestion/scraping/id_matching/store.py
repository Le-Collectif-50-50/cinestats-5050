"""Journal des tentatives, séparant propositions confirmées et cas à examiner."""

import json
from dataclasses import asdict

from sqlalchemy import text

REVIEW_STATUSES = {"a_revoir", "ambigu", "non_trouve", "bloque", "erreur"}


def exclude_processed(engine, pending):
    """Rejouer une erreur technique, mais conserver les conclusions métier inchangées."""
    with engine.connect() as connection:
        results = connection.execute(
            text("""
            SELECT visa, provider, evidence -> 'reference' AS reference
            FROM ops.id_matching_confirmed
            UNION ALL
            SELECT visa, provider, evidence -> 'reference' AS reference
            FROM ops.id_matching_review
            WHERE status IN ('a_revoir', 'ambigu', 'non_trouve')
        """)
        )
        done = {}
        for visa, provider, reference in results:
            done.setdefault((visa, provider), []).append(reference)
    remaining = []
    for reference, providers in pending:
        selected = [
            p for p in providers if asdict(reference) not in done.get((reference.visa, p), [])
        ]
        if selected:
            remaining.append((reference, selected))
    return remaining


def destination(result):
    if result["status"] == "trouve":
        value = result.get("confirmed_id", "")
        if not value.isascii() or not value.isdecimal() or int(value) < 1:
            raise ValueError("Un résultat confirmé exige un identifiant numérique positif.")
        return "id_matching_confirmed"
    if result["status"] not in REVIEW_STATUSES or result.get("confirmed_id"):
        raise ValueError("Résultat de revue incohérent.")
    return "id_matching_review"


def save_result(engine, run_id, result):
    table = destination(result)  # Valeur issue d'une liste fermée, jamais de l'utilisateur.
    with engine.begin() as connection:
        connection.execute(
            text(f"""
            INSERT INTO ops.{table}
                (run_id, visa, provider, status, proposed_id, source_title,
                 reason, checked_at, evidence)
            VALUES (CAST(:run_id AS uuid), :visa, :provider, :status, :proposed_id,
                    :source_title, :reason, CAST(:checked_at AS timestamptz),
                    CAST(:evidence AS jsonb))
        """),
            {
                "run_id": str(run_id),
                "visa": result["visa"],
                "provider": result["provider"],
                "status": result["status"],
                "proposed_id": result.get("confirmed_id") or None,
                "source_title": result["reference"]["title"],
                "reason": result["reason"],
                "checked_at": result["checked_at"],
                "evidence": json.dumps(result, ensure_ascii=False),
            },
        )


def check_tables(engine):
    # Vérifier avant les requêtes réseau ; aucun DDL implicite.
    with engine.connect() as connection:
        for table in ("id_matching_confirmed", "id_matching_review"):
            connection.execute(text(f"SELECT run_id FROM ops.{table} LIMIT 0"))
            allowed = connection.scalar(
                text("SELECT has_table_privilege(current_user, :table, 'INSERT')"),
                {"table": "ops." + table},
            )
            if not allowed:
                raise PermissionError(f"Droit INSERT requis sur ops.{table}.")
