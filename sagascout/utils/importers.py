"""Importers for common genealogy file formats (GEDCOM, JSON)."""

import json
import re
from typing import Dict, Any, List, Optional, Tuple


class GEDCOMImporter:
    """
    Parser for GEDCOM (.ged) files — the standard genealogy interchange format.

    Produces a normalized dict with ``individuals`` and ``relationships`` lists
    that are compatible with the rest of the SagaScout tree layer.
    """

    # GEDCOM tag constants
    _TAG_INDI = "INDI"
    _TAG_FAM = "FAM"
    _TAG_NAME = "NAME"
    _TAG_SEX = "SEX"
    _TAG_BIRT = "BIRT"
    _TAG_DEAT = "DEAT"
    _TAG_MARR = "MARR"
    _TAG_DATE = "DATE"
    _TAG_PLAC = "PLAC"
    _TAG_HUSB = "HUSB"
    _TAG_WIFE = "WIFE"
    _TAG_CHIL = "CHIL"
    _TAG_NOTE = "NOTE"
    _TAG_OCCU = "OCCU"

    def __init__(self):
        """Initialise the importer with empty state."""
        self._individuals: Dict[str, Dict[str, Any]] = {}
        self._families: Dict[str, Dict[str, Any]] = {}

    def parse_file(self, filepath: str) -> Dict[str, Any]:
        """
        Parse a GEDCOM file from disk.

        Args:
            filepath: Absolute or relative path to the .ged file.

        Returns:
            Normalised tree dict with ``individuals`` and ``relationships``.
        """
        with open(filepath, "r", encoding="utf-8", errors="replace") as fh:
            content = fh.read()
        return self.parse_string(content)

    def parse_string(self, content: str) -> Dict[str, Any]:
        """
        Parse GEDCOM content from a string.

        Args:
            content: Raw GEDCOM text.

        Returns:
            Normalised tree dict with ``individuals`` and ``relationships``.
        """
        self._individuals = {}
        self._families = {}

        lines = content.splitlines()
        records = self._split_into_records(lines)

        for record in records:
            if not record:
                continue
            first = record[0]
            # Level-0 lines look like: 0 @I1@ INDI  or  0 HEAD
            parts = first.split(None, 2)
            if len(parts) < 2:
                continue
            tag_or_xref = parts[1] if len(parts) >= 2 else ""
            if tag_or_xref.startswith("@") and len(parts) >= 3:
                xref = tag_or_xref
                record_type = parts[2].strip()
                if record_type == self._TAG_INDI:
                    self._parse_individual(xref, record[1:])
                elif record_type == self._TAG_FAM:
                    self._parse_family(xref, record[1:])

        return self._build_tree_dict()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _split_into_records(self, lines: List[str]) -> List[List[str]]:
        """Split GEDCOM lines into level-0 record groups."""
        records: List[List[str]] = []
        current: List[str] = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("0 "):
                if current:
                    records.append(current)
                current = [stripped]
            else:
                current.append(stripped)
        if current:
            records.append(current)
        return records

    def _parse_tag_line(self, line: str) -> Tuple[int, str, str]:
        """Return (level, tag, value) for a GEDCOM line."""
        parts = line.split(None, 2)
        level = int(parts[0]) if parts else 0
        tag = parts[1] if len(parts) > 1 else ""
        value = parts[2] if len(parts) > 2 else ""
        return level, tag, value

    def _parse_individual(self, xref: str, lines: List[str]) -> None:
        """Parse an INDI record and store in self._individuals."""
        person: Dict[str, Any] = {
            "id": self._clean_xref(xref),
            "name": None,
            "sex": None,
            "birth_date": None,
            "birth_place": None,
            "death_date": None,
            "death_place": None,
            "occupation": None,
            "notes": [],
        }

        i = 0
        while i < len(lines):
            level, tag, value = self._parse_tag_line(lines[i])
            if tag == self._TAG_NAME:
                person["name"] = self._clean_name(value)
            elif tag == self._TAG_SEX:
                person["sex"] = value.strip()
            elif tag == self._TAG_OCCU:
                person["occupation"] = value.strip()
            elif tag == self._TAG_NOTE:
                person["notes"].append(value.strip())
            elif tag == self._TAG_BIRT:
                # Collect sub-tags at level+1
                birth = self._parse_event_block(lines, i + 1, level + 1)
                person["birth_date"] = birth.get("date")
                person["birth_place"] = birth.get("place")
            elif tag == self._TAG_DEAT:
                death = self._parse_event_block(lines, i + 1, level + 1)
                person["death_date"] = death.get("date")
                person["death_place"] = death.get("place")
            i += 1

        self._individuals[xref] = person

    def _parse_event_block(
        self, lines: List[str], start: int, expected_level: int
    ) -> Dict[str, str]:
        """Parse DATE/PLAC sub-tags from an event block."""
        event: Dict[str, str] = {}
        for line in lines[start:]:
            lvl, tag, value = self._parse_tag_line(line)
            if lvl < expected_level:
                break
            if lvl == expected_level:
                if tag == self._TAG_DATE:
                    event["date"] = value.strip()
                elif tag == self._TAG_PLAC:
                    event["place"] = value.strip()
        return event

    def _parse_family(self, xref: str, lines: List[str]) -> None:
        """Parse a FAM record and store in self._families."""
        family: Dict[str, Any] = {
            "id": self._clean_xref(xref),
            "husband": None,
            "wife": None,
            "children": [],
            "marriage_date": None,
            "marriage_place": None,
        }

        i = 0
        while i < len(lines):
            level, tag, value = self._parse_tag_line(lines[i])
            if tag == self._TAG_HUSB:
                family["husband"] = self._clean_xref(value.strip())
            elif tag == self._TAG_WIFE:
                family["wife"] = self._clean_xref(value.strip())
            elif tag == self._TAG_CHIL:
                family["children"].append(self._clean_xref(value.strip()))
            elif tag == self._TAG_MARR:
                marr = self._parse_event_block(lines, i + 1, level + 1)
                family["marriage_date"] = marr.get("date")
                family["marriage_place"] = marr.get("place")
            i += 1

        self._families[xref] = family

    def _build_tree_dict(self) -> Dict[str, Any]:
        """Combine parsed individuals and families into the normalised format."""
        individuals = list(self._individuals.values())

        relationships: List[Dict[str, Any]] = []
        for family in self._families.values():
            husb = family["husband"]
            wife = family["wife"]
            children = family["children"]

            # Spouse relationship
            if husb and wife:
                relationships.append({
                    "type": "spouse",
                    "person1": husb,
                    "person2": wife,
                    "marriage_date": family.get("marriage_date"),
                    "marriage_place": family.get("marriage_place"),
                })

            # Parent→child relationships
            for child in children:
                if husb:
                    relationships.append({
                        "type": "parent",
                        "parent": husb,
                        "child": child,
                        "parent_role": "father",
                    })
                if wife:
                    relationships.append({
                        "type": "parent",
                        "parent": wife,
                        "child": child,
                        "parent_role": "mother",
                    })

        return {
            "source": "gedcom",
            "individuals": individuals,
            "relationships": relationships,
            "family_units": list(self._families.values()),
        }

    @staticmethod
    def _clean_xref(xref: str) -> str:
        """Strip @ delimiters from GEDCOM cross-references."""
        return xref.strip().strip("@")

    @staticmethod
    def _clean_name(raw: str) -> str:
        """Remove GEDCOM surname slashes and extra whitespace from a name."""
        return re.sub(r"/([^/]*)/", r"\1", raw).strip()


class JSONImporter:
    """
    Importer for JSON genealogy data.

    Accepts two layouts:

    1. **Native SagaScout format** — a dict with ``individuals`` and
       ``relationships`` keys (already in the internal format).

    2. **Generic flat format** — a dict/list with person objects that contain
       common genealogy keys (``id``, ``name``, ``father_id``, ``mother_id``,
       ``birth_date``, ``death_date``, etc.).  The importer normalises these
       into the standard internal format.
    """

    def parse_file(self, filepath: str) -> Dict[str, Any]:
        """
        Parse a JSON file from disk.

        Args:
            filepath: Absolute or relative path to the JSON file.

        Returns:
            Normalised tree dict with ``individuals`` and ``relationships``.
        """
        with open(filepath, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return self.parse_dict(data)

    def parse_string(self, content: str) -> Dict[str, Any]:
        """
        Parse JSON genealogy data from a string.

        Args:
            content: Raw JSON string.

        Returns:
            Normalised tree dict with ``individuals`` and ``relationships``.
        """
        data = json.loads(content)
        return self.parse_dict(data)

    def parse_dict(self, data: Any) -> Dict[str, Any]:
        """
        Normalise a Python dict/list into the standard tree format.

        Args:
            data: Parsed JSON value (dict or list).

        Returns:
            Normalised tree dict with ``individuals`` and ``relationships``.
        """
        # Wrap bare list into flat-format normalisation
        if isinstance(data, list):
            return self._normalise_flat(data)

        # Already in native format
        if "individuals" in data and "relationships" in data:
            return self._normalise_native(data)

        # Generic flat format: look for a list of person records
        persons_key = next(
            (k for k in data if isinstance(data[k], list) and data[k]), None
        )
        if persons_key:
            return self._normalise_flat(data[persons_key])

        return {"source": "json", "individuals": [], "relationships": []}

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _normalise_native(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Return native format data with source tag added."""
        result = dict(data)
        result["source"] = "json"
        return result

    def _normalise_flat(self, persons: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Convert a flat list of person dicts to the internal format."""
        individuals: List[Dict[str, Any]] = []
        relationships: List[Dict[str, Any]] = []

        for person in persons:
            # Build normalised individual record
            ind: Dict[str, Any] = {
                "id": str(person.get("id", "")),
                "name": person.get("name") or person.get("full_name"),
                "sex": person.get("sex") or person.get("gender"),
                "birth_date": person.get("birth_date") or person.get("dob"),
                "birth_place": person.get("birth_place"),
                "death_date": person.get("death_date") or person.get("dod"),
                "death_place": person.get("death_place"),
                "occupation": person.get("occupation"),
                "notes": person.get("notes", []),
            }
            # Carry over any extra keys
            for key, val in person.items():
                if key not in ind:
                    ind[key] = val
            individuals.append(ind)

            # Derive parent relationships from father_id / mother_id
            pid = str(person.get("id", ""))
            father_id = person.get("father_id")
            mother_id = person.get("mother_id")
            if father_id:
                relationships.append({
                    "type": "parent",
                    "parent": str(father_id),
                    "child": pid,
                    "parent_role": "father",
                })
            if mother_id:
                relationships.append({
                    "type": "parent",
                    "parent": str(mother_id),
                    "child": pid,
                    "parent_role": "mother",
                })

        return {
            "source": "json",
            "individuals": individuals,
            "relationships": relationships,
        }


def load_tree(path: str) -> Dict[str, Any]:
    """
    Convenience function: detect format by file extension and import.

    Args:
        path: Path to a ``.ged`` or ``.json`` file.

    Returns:
        Normalised tree dict with ``individuals`` and ``relationships``.

    Raises:
        ValueError: If the file extension is not recognised.
    """
    lower = path.lower()
    if lower.endswith(".ged"):
        return GEDCOMImporter().parse_file(path)
    if lower.endswith(".json"):
        return JSONImporter().parse_file(path)
    raise ValueError(
        f"Unsupported file format for '{path}'. "
        "Supported extensions: .ged, .json"
    )
