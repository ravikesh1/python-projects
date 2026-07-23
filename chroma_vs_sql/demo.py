"""
ChromaDB vs SQL — Side-by-side comparison demo.

Run: python -m chroma_vs_sql.demo
"""

from chroma_vs_sql.sample_data import DOCUMENTS, PATIENTS
from chroma_vs_sql import sql_store, chroma_store


def print_header(title: str) -> None:
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}")


def print_subheader(title: str) -> None:
    print(f"\n  --- {title} ---")


def format_chroma_results(results: dict) -> None:
    for i, (doc, meta, dist) in enumerate(
        zip(results["documents"][0], results["metadatas"][0], results["distances"][0])
    ):
        similarity = round(1 - dist, 3)
        print(f"    {i + 1}. [{meta['category']}] {doc[:80]}...")
        print(f"       Similarity score: {similarity}")


def main() -> None:
    # ── Setup both stores ──
    print("Setting up databases...")
    sql_store.setup(PATIENTS)
    chroma_store.setup(DOCUMENTS)
    print("Done! Both databases loaded with healthcare data.\n")

    # ══════════════════════════════════════════════════════════
    # DEMO 1: Plain English vs Exact Match
    # ══════════════════════════════════════════════════════════
    print_header("DEMO 1: 'I have chest pain' — How each database handles it")

    print_subheader("ChromaDB (semantic search)")
    print('  Query: "I have chest pain and trouble breathing"')
    print()
    results = chroma_store.query_semantic("I have chest pain and trouble breathing")
    format_chroma_results(results)

    print_subheader("SQL (exact match)")
    print('  Query: SELECT * FROM patients WHERE condition LIKE "%chest%"')
    print()
    sql_results = sql_store.query_like("chest")
    if sql_results:
        for r in sql_results:
            print(f"    - {r['name']}, {r['condition']}")
    else:
        print('    No results! "chest" doesn\'t appear in any condition column.')
        print('    SQL needs exact words. Try "hypertension" or "diabetes" instead.')

    # ══════════════════════════════════════════════════════════
    # DEMO 2: Synonyms & Related Concepts
    # ══════════════════════════════════════════════════════════
    print_header("DEMO 2: 'mental health' — Understanding meaning vs matching words")

    print_subheader("ChromaDB (understands meaning)")
    print('  Query: "mental health problems and feeling worried"')
    print()
    results = chroma_store.query_semantic("mental health problems and feeling worried")
    format_chroma_results(results)

    print_subheader("SQL (literal match)")
    print('  Query: SELECT * FROM patients WHERE condition LIKE "%mental%"')
    print()
    sql_results = sql_store.query_like("mental")
    if sql_results:
        for r in sql_results:
            print(f"    - {r['name']}, {r['condition']}")
    else:
        print('    No results! The word "mental" isn\'t in the condition column.')
        print('    The patient has "generalized anxiety" — SQL can\'t make that connection.')

    # ══════════════════════════════════════════════════════════
    # DEMO 3: What SQL does best — structured queries
    # ══════════════════════════════════════════════════════════
    print_header("DEMO 3: What SQL does best — structured queries")

    print_subheader("Find all cardiology patients")
    print("  Query: SELECT * FROM patients WHERE department = 'cardiology'")
    print()
    for r in sql_store.query_exact("cardiology"):
        print(f"    - {r['name']}, age {r['age']}, {r['condition']} ({r['status']})")

    print_subheader("Active patients over 50")
    print("  Query: SELECT * FROM patients WHERE age >= 50 AND status = 'active'")
    print()
    for r in sql_store.query_filter(50, "active"):
        print(f"    - {r['name']}, age {r['age']}, {r['condition']}")

    print_subheader("Patients per department (aggregation)")
    print("  Query: SELECT department, COUNT(*) FROM patients GROUP BY department")
    print()
    for r in sql_store.query_aggregate():
        print(f"    - {r['department']}: {r['patient_count']} patients")

    # ══════════════════════════════════════════════════════════
    # DEMO 4: ChromaDB with metadata filter
    # ══════════════════════════════════════════════════════════
    print_header("DEMO 4: ChromaDB can filter too — semantic + metadata")

    print_subheader("Breathing problems, but only in pulmonology docs")
    print('  Query: "difficulty breathing" + filter: category=pulmonology')
    print()
    results = chroma_store.query_with_filter("difficulty breathing", "pulmonology")
    format_chroma_results(results)

    # ══════════════════════════════════════════════════════════
    # DEMO 5: The key difference
    # ══════════════════════════════════════════════════════════
    print_header("DEMO 5: Same question, different approaches")

    question = "What should I do about sugar problems?"

    print_subheader("ChromaDB — understands 'sugar problems' = diabetes")
    print(f'  Query: "{question}"')
    print()
    results = chroma_store.query_semantic(question, n_results=2)
    format_chroma_results(results)

    print_subheader("SQL — searches for literal 'sugar'")
    print(f'  Query: SELECT * FROM patients WHERE condition LIKE "%sugar%"')
    print()
    sql_results = sql_store.query_like("sugar")
    if sql_results:
        for r in sql_results:
            print(f"    - {r['name']}, {r['condition']}")
    else:
        print('    No results! SQL doesn\'t know "sugar" relates to "diabetes".')
        print('    You\'d need: WHERE condition LIKE "%diabetes%" — but the user didn\'t say that.')

    # ══════════════════════════════════════════════════════════
    print_header("SUMMARY")
    print("""
  ChromaDB:  Ask in plain English → finds documents by MEANING
             Best for: search, Q&A, RAG, recommendations

  SQL:       Write structured queries → finds rows by EXACT VALUES
             Best for: filters, counts, joins, transactions

  Together:  SQL stores your business data (patients, orders, users)
             ChromaDB stores your knowledge base for AI-powered search
""")


if __name__ == "__main__":
    main()
