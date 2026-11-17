import json
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest

from ingestion.scraping.date_utils import parse_duration, parse_release_date
from ingestion.scraping.allocine.allocine_scraper import AllocineScraper


@pytest.mark.parametrize("tag", ["a", "span"])
def test_release_date_from_link_or_span(tag):
    html = (
        f'<div class="meta-body-info"><{tag} class="date blue-link">'
        f'27 avril 2022</{tag}> | 0h 26min</div>'
        '<div class="other"><a class="date blue-link">1 janvier 2024</a></div>'
    )
    value = AllocineScraper().extract_film_details(html)["release_date"]
    assert parse_release_date(value) == date(2022, 4, 27)


def test_missing_release_date_does_not_use_another_section():
    html = '<div class="meta-body-info">0h 26min</div><span class="date blue-link">1 janvier 2024</span>'
    assert AllocineScraper().extract_film_details(html)["release_date"] is None


@pytest.mark.parametrize(
    "value, expected",
    [
        ("12 janvier 2023", date(2023, 1, 12)),
        ("01 février 2020", date(2020, 2, 1)),
        ("31 décembre 1999", date(1999, 12, 31)),
        ("29 octobre 2025", date(2025, 10, 29)),
        ("", None),
        (None, None),
        ("not a date", None),
    ],
)
def test_parse_release_date(value, expected):
    assert parse_release_date(value) == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        ("2h00min", 120),
        ("1h45min", 105),
        ("0h10min", 10),
        ("1h", 60),
        ("90min", 90),
        ("3h40min", 220),
        ("1 h 45 min", 105),
        ("0min", None),
        ("", None),
        ("   ", None),
        (None, None),
        ("weird input", None),
    ],
)
def test_parse_duration(value, expected):
    assert parse_duration(value) == expected


def test_cli_spec_without_backend(tmp_path):
    """Exercise startup with only ingestion Python files in the deployment."""
    repo_root = Path(__file__).resolve().parents[2]
    for source in (repo_root / "ingestion").rglob("*.py"):
        destination = tmp_path / source.relative_to(repo_root)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)

    # Isolated Python ignores PYTHONPATH and the original repository.
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            "import importlib.util, runpy, sys; "
            "sys.path.insert(0, sys.argv[1]); "
            "assert importlib.util.find_spec('backend') is None; "
            "sys.argv = ['ingestion/scraping/allocine/main.py', 'spec']; "
            "runpy.run_path(sys.argv[0], run_name='__main__')",
            str(tmp_path),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    message = json.loads(result.stdout)
    assert message["type"] == "SPEC"
    assert "connectionSpecification" in message["spec"]
