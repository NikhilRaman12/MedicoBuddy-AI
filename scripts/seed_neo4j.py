"""Seed Neo4j knowledge graph with initial data from Cypher files."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from medicobuddy.config import get_settings
from medicobuddy.knowledge_graph.client import Neo4jClient


SEED_DIR = Path(__file__).resolve().parent.parent / "data" / "seed"


async def seed_database() -> None:
    """Load all seed Cypher files into Neo4j."""
    settings = get_settings()
    client = Neo4jClient(settings)

    print("Connecting to Neo4j...")
    await client.connect()

    print("Initializing schema (constraints + indexes)...")
    await client.init_schema()

    # Load seed files in order
    seed_files = sorted(SEED_DIR.glob("*.cypher"))
    for seed_file in seed_files:
        print(f"Loading {seed_file.name}...")
        cypher_text = seed_file.read_text(encoding="utf-8")

        # Split on semicolons to get individual statements
        statements = [
            stmt.strip()
            for stmt in cypher_text.split(";")
            if stmt.strip() and not stmt.strip().startswith("//")
        ]

        for stmt in statements:
            try:
                await client.execute_write(stmt)
            except Exception as e:
                print(f"  Warning: {e}")

    print(f"Loaded {len(seed_files)} seed files.")
    await client.close()
    print("Done.")


if __name__ == "__main__":
    asyncio.run(seed_database())
