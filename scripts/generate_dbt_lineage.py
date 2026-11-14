"""Produire un document GitHub depuis le manifest dbt, sans dépendance externe."""

import argparse
from collections import Counter
import html
import json
from pathlib import Path
from urllib.parse import quote


RESOURCE_TYPES = {"source", "model", "seed", "snapshot"}


def text(value):
    """Protéger les tableaux Markdown et les libellés Mermaid."""
    return html.escape(str(value), quote=True).replace("|", "&#124;").replace("\n", " ")


def render(manifest, source_url, revision_date):
    resources = {**manifest.get("sources", {}), **manifest.get("nodes", {})}
    nodes = {
        key: node
        for key, node in sorted(resources.items())
        if node["resource_type"] in RESOURCE_TYPES
        and node.get("config", {}).get("enabled", True)
    }
    if not nodes:
        raise ValueError("Le manifest ne contient aucune ressource de lineage.")
    edges = set()
    for key, node in nodes.items():
        for parent in node.get("depends_on", {}).get("nodes", []):
            if parent not in nodes:
                raise ValueError(f"Dépendance absente du lineage : {parent} -> {key}")
            edges.add((parent, key))

    def label(key):
        node = nodes[key]
        name = node.get("identifier") or node.get("alias") or node["name"]
        return f"{node['schema']}.{name}"

    def link(key):
        node = nodes[key]
        path = node["original_file_path"]
        if node["package_name"] != manifest["metadata"]["project_name"]:
            path = f"dbt_packages/{node['package_name']}/{path}"
            return f"{text(label(key))} (`{text(path)}`)"
        url = source_url.rstrip("/") + "/ingestion/dbt/" + quote(path, safe="/")
        return f"[{text(label(key))}]({url})"

    ids = {key: f"n{index}" for index, key in enumerate(nodes)}

    def diagram_node(key, indent="  "):
        opening, closing = ('(["', '"])') if nodes[key]["resource_type"] == "source" else ('["', '"]')
        return f"{indent}{ids[key]}{opening}{text(label(key))}{closing}"

    counts = Counter(node["resource_type"] for node in nodes.values())
    lines = [
        "# Lineage dbt — ingestion RIC", "",
        "**Owner:** Joel Teixeira", "",
        f"**Dernière révision:** {revision_date}", "",
        "**Status:** actif", "",
        "Dépendances déclarées dans le projet dbt, des sources vers les modèles consommateurs.",
        f"[Version du code analysée]({source_url}).", "",
        f"{counts['source']} sources, {counts['model']} modèles, "
        f"{counts['seed']} seeds, {counts['snapshot']} snapshots ; {len(edges)} dépendances directes.",
        "",
        "Généré avec `dbt parse` puis `scripts/generate_dbt_lineage.py`. "
        "Aucune connexion à PostgreSQL. Les flèches suivent les appels `ref()` et `source()` "
        "du manifest ; les références SQL écrites en dur ne sont pas déduites.", "",
        "Ce document décrit les dépendances entre relations, pas entre colonnes. "
        "Il ne prouve ni la présence des tables en base, ni le succès des traitements. "
        "Les tests, analyses, macros, modèles désactivés et traitements externes "
        "Airbyte/Prefect/scraping sont hors graphe.", "",
        "## Lineage dbt complet", "",
        "Cette vue rassemble toutes les relations actives du manifest, y compris celles "
        "sans dépendance. Suivre les flèches de gauche à droite pour parcourir les chaînes "
        "des sources brutes jusqu’aux modèles finaux et opérationnels. "
        "Les cadres regroupent les relations par schéma ; les sources brutes sont arrondies.", "",
        "```mermaid", "flowchart LR",
    ]
    layer_order = {name: index for index, name in enumerate(["raw", "staging", "intermediate", "fnl", "ops"])}
    all_schemas = sorted(
        {node["schema"] for node in nodes.values()},
        key=lambda name: (layer_order.get(name, len(layer_order)), name),
    )
    for index, schema in enumerate(all_schemas):
        lines.append(f'  subgraph s{index}["{text(schema)}"]')
        lines.extend(diagram_node(key, "    ") for key, node in nodes.items() if node["schema"] == schema)
        lines.append("  end")
    lines.extend(f"  {ids[a]} --> {ids[b]}" for a, b in sorted(edges))
    lines.extend([
        "```", "",
        "## Vues détaillées par schéma", "",
        "<details>", "<summary>Afficher les diagrammes par schéma consommateur</summary>", "",
        "Chaque diagramme montre les relations du schéma et leurs parents directs. "
        "Une relation peut donc apparaître dans plusieurs diagrammes. "
        "Les sources brutes sont arrondies ; les transformations sont rectangulaires.", "",
    ])
    schemas = sorted({node["schema"] for node in nodes.values() if node["resource_type"] != "source"})
    for schema in schemas:
        children = {key for key, node in nodes.items() if node["schema"] == schema and node["resource_type"] != "source"}
        schema_edges = sorted((a, b) for a, b in edges if b in children)
        visible = children | {a for a, _ in schema_edges}
        lines.extend([f"### {text(schema)}", "", "```mermaid", "flowchart LR"])
        lines.extend(diagram_node(key) for key in sorted(visible))
        lines.extend(f"  {ids[a]} --> {ids[b]}" for a, b in schema_edges)
        lines.extend(["```", ""])
    lines.extend([
        "</details>", "",
        "## Inventaire et dépendances directes", "",
        "Les liens ouvrent les définitions à la version du code analysée.", "",
        "| Relation | Type | Matérialisation | Parents directs |",
        "| --- | --- | --- | --- |",
    ])
    for key, node in nodes.items():
        parents = ", ".join(link(a) for a, b in sorted(edges) if b == key) or "—"
        materialized = node.get("config", {}).get("materialized", "—")
        lines.append(f"| {link(key)} | {node['resource_type']} | {text(materialized)} | {parents} |")
    lines.extend([
        "", "## Historique du document", "",
        "| # | Date | Auteur | Observations |", "| --- | --- | --- | --- |",
        f"| 1 | {revision_date} | Joel Teixeira | État généré depuis la version du code liée ci-dessus. |",
        "", "Les versions précédentes restent disponibles dans l’historique Git de la branche `dbt-lineage`.", "",
    ])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--source-url", required=True, help="URL GitHub /tree/<commit>")
    parser.add_argument("--revision-date", required=True, help="Date du commit analysé (YYYY-MM-DD)")
    args = parser.parse_args()
    content = render(json.loads(args.manifest.read_text()), args.source_url, args.revision_date)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
