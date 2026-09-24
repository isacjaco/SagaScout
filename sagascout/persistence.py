"""
Persistence layer for SagaScout agents.

Provides :func:`save_agent_state` and :func:`load_agent_state` to serialise
and restore Scout, Archivist, and NarrativeMemory instances.
"""

import json
from pathlib import Path
from typing import Any, Dict, Type

import os

def _get_secure_path(filepath: str, base_dir: str = None) -> Path:
    if base_dir is None:
        base_dir = os.environ.get("SAGASCOUT_DATA_DIR", ".")

    base = Path(base_dir).resolve()
    target = Path(filepath)

    if not target.is_absolute():
        target = base / target

    target = target.resolve()

    try:
        target.relative_to(base)
    except ValueError:
        raise PermissionError(f"Path traversal attempt: {filepath} is outside {base}")

    return target



def save_agent_state(agent: Any, filepath: str, base_dir: str = None) -> None:
    """
    Save the state of a Scout, Archivist, or NarrativeMemory to a JSON file.

    For agents that expose a :meth:`to_json` method the serialised output also
    includes the agent ``name`` and ``config`` so they can be restored
    faithfully with :func:`load_agent_state`.

    Args:
        agent: Agent or NarrativeMemory instance to serialise
        filepath: Destination file path (created or overwritten)
        base_dir: Optional base directory to restrict path traversal

    Raises:
        TypeError: If the agent type is not supported
    """
    from sagascout.agents.scout import Scout
    from sagascout.agents.archivist import Archivist
    from sagascout.utils.narrative_memory import NarrativeMemory

    if isinstance(agent, (Scout, Archivist)):
        state = agent.to_json()
        state["__type__"] = type(agent).__name__
        state["__name__"] = agent.name
        state["__config__"] = agent.config
    elif isinstance(agent, NarrativeMemory):
        state = agent.to_json()
        state["__type__"] = "NarrativeMemory"
    else:
        raise TypeError(
            f"Unsupported agent type: {type(agent).__name__}. "
            "Supported types: Scout, Archivist, NarrativeMemory"
        )

    secure_path = _get_secure_path(filepath, base_dir)
    secure_path.write_text(json.dumps(state, indent=2), encoding="utf-8")


def load_agent_state(agent_class: Type, filepath: str, base_dir: str = None) -> Any:
    """
    Restore an agent or NarrativeMemory from a JSON file.

    Args:
        agent_class: The class to instantiate. Must be one of
            :class:`~sagascout.agents.scout.Scout`,
            :class:`~sagascout.agents.archivist.Archivist`, or
            :class:`~sagascout.utils.narrative_memory.NarrativeMemory`.
        filepath: Source file path previously written by :func:`save_agent_state`
        base_dir: Optional base directory to restrict path traversal

    Returns:
        Restored instance of *agent_class*

    Raises:
        TypeError: If *agent_class* is not supported
        FileNotFoundError: If *filepath* does not exist
    """
    from sagascout.agents.scout import Scout
    from sagascout.agents.archivist import Archivist
    from sagascout.utils.narrative_memory import NarrativeMemory

    data: Dict[str, Any] = json.loads(
        _get_secure_path(filepath, base_dir).read_text(encoding="utf-8")
    )

    if agent_class is Scout:
        return Scout.from_json(
            data,
            name=data.get("__name__", "Scout"),
            config=data.get("__config__", {}),
        )
    elif agent_class is Archivist:
        return Archivist.from_json(
            data,
            name=data.get("__name__", "Archivist"),
            config=data.get("__config__", {}),
        )
    elif agent_class is NarrativeMemory:
        return NarrativeMemory.from_json(data)
    else:
        raise TypeError(
            f"Unsupported agent class: {agent_class.__name__}. "
            "Supported classes: Scout, Archivist, NarrativeMemory"
        )
