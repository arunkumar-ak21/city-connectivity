"""
Ecosystem Detector
==================
Given the file listing from a repository's root directory, determines
which programming language / ecosystem(s) the project uses by matching
against well-known dependency manifest filenames.

Each ecosystem is associated with a set of *indicator files*.  When
multiple ecosystems are detected the detector returns all of them,
ranked by the number of matching indicator files (most likely first).
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Indicator files → ecosystem mapping
# ---------------------------------------------------------------------------
# Keys are lowercase filenames; values are (ecosystem, manifest_flag).
# manifest_flag=True means the file should be fetched and parsed.
INDICATOR_FILES: dict[str, tuple[str, bool]] = {
    # Python
    "requirements.txt":     ("python", True),
    "requirements.lock":    ("python", False),
    "setup.py":             ("python", True),
    "setup.cfg":            ("python", True),
    "pipfile":              ("python", True),
    "pipfile.lock":         ("python", False),
    "pyproject.toml":       ("python", True),
    "poetry.lock":          ("python", False),
    # Node.js
    "package.json":         ("node", True),
    "package-lock.json":    ("node", False),
    "yarn.lock":            ("node", False),
    "pnpm-lock.yaml":       ("node", False),
    # Java
    "pom.xml":              ("java", True),
    "build.gradle":         ("java", True),
    "build.gradle.kts":     ("java", True),
    # Go
    "go.mod":               ("go", True),
    "go.sum":               ("go", False),
    # Ruby
    "gemfile":              ("ruby", True),
    "gemfile.lock":         ("ruby", False),
    # Rust
    "cargo.toml":           ("rust", True),
    "cargo.lock":           ("rust", False),
    # PHP
    "composer.json":        ("php", True),
    "composer.lock":        ("php", False),
}


class EcosystemDetector:
    """
    Detect which ecosystems a repository uses based on its root file listing.

    Attributes
    ----------
    ecosystems : dict[str, EcosystemInfo]
        Mapping of ecosystem name → detected info (manifest paths, has lock file).
    """

    def __init__(self) -> None:
        self.ecosystems: dict[str, dict] = {}

    def detect(self, file_listing: list[dict]) -> dict[str, dict]:
        """
        Analyse a GitHub Contents-API file listing and return detected
        ecosystems.

        Parameters
        ----------
        file_listing : list[dict]
            Each dict must have at least a ``"name"`` key.

        Returns
        -------
        dict[str, dict]
            Keys are ecosystem names (``"python"``, ``"node"``, …).
            Values contain::

                {
                    "manifest_files": ["requirements.txt", ...],
                    "has_lock_file": True/False,
                    "indicator_count": 3,
                }
        """
        self.ecosystems = {}

        for item in file_listing:
            name_lower = item.get("name", "").lower()
            if name_lower not in INDICATOR_FILES:
                continue

            ecosystem, is_manifest = INDICATOR_FILES[name_lower]

            if ecosystem not in self.ecosystems:
                self.ecosystems[ecosystem] = {
                    "manifest_files": [],
                    "lock_files": [],
                    "has_lock_file": False,
                    "indicator_count": 0,
                }

            info = self.ecosystems[ecosystem]
            info["indicator_count"] += 1

            if is_manifest:
                # Store the *original-case* filename from the API
                info["manifest_files"].append(item["name"])
            else:
                info["has_lock_file"] = True
                info["lock_files"].append(item["name"])

        # Sort by indicator count descending (primary ecosystem first)
        self.ecosystems = dict(
            sorted(self.ecosystems.items(), key=lambda kv: -kv[1]["indicator_count"])
        )

        if self.ecosystems:
            logger.info(
                "Detected ecosystems: %s",
                ", ".join(f"{k} ({v['indicator_count']} indicators)" for k, v in self.ecosystems.items()),
            )
        else:
            logger.warning("No known dependency manifests detected in repository root.")

        return self.ecosystems
