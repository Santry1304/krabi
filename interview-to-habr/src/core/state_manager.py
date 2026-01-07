"""Project state management with JSON persistence."""

from pathlib import Path
from datetime import datetime
from typing import Optional, Any
import json
import logging
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ProjectState(BaseModel):
    """Project state model."""
    version: str = "1.0"
    project_name: str
    created_at: datetime
    updated_at: datetime
    config: dict = Field(default_factory=dict)
    input: dict = Field(default_factory=dict)
    pipeline: dict = Field(default_factory=dict)
    materials: dict = Field(default_factory=dict)
    statistics: dict = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class StateManager:
    """Manages project state with JSON persistence."""

    def __init__(self, project_dir: Path):
        """
        Initialize state manager.

        Args:
            project_dir: Project directory path
        """
        self.project_dir = Path(project_dir)
        self.state_file = self.project_dir / "state.json"
        self._state: Optional[ProjectState] = None

    def load(self) -> Optional[ProjectState]:
        """
        Load state from file.

        Returns:
            ProjectState if file exists, None otherwise
        """
        if self.state_file.exists():
            try:
                data = json.loads(self.state_file.read_text(encoding='utf-8'))

                # Parse datetime strings
                if 'created_at' in data and isinstance(data['created_at'], str):
                    data['created_at'] = datetime.fromisoformat(data['created_at'])
                if 'updated_at' in data and isinstance(data['updated_at'], str):
                    data['updated_at'] = datetime.fromisoformat(data['updated_at'])

                self._state = ProjectState(**data)
                logger.info(f"Loaded state from {self.state_file}")
                return self._state
            except Exception as e:
                logger.error(f"Failed to load state: {e}")
                return None
        return None

    def save(self):
        """Save state to file."""
        if self._state:
            self._state.updated_at = datetime.now()

            # Convert to dict
            data = self._state.model_dump()

            # Format datetimes
            data['created_at'] = data['created_at'].isoformat()
            data['updated_at'] = data['updated_at'].isoformat()

            self.state_file.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding='utf-8'
            )
            logger.info(f"Saved state to {self.state_file}")

    def create_new(self, project_name: str, config: dict) -> ProjectState:
        """
        Create new project state.

        Args:
            project_name: Project name
            config: Configuration dictionary

        Returns:
            New ProjectState
        """
        now = datetime.now()

        # Initialize pipeline stages
        stages = {}
        stage_names = [
            "load", "format", "compare", "plan", "write",
            "merge", "edit", "analyze", "select", "generate"
        ]

        for i, name in enumerate(stage_names, 1):
            stages[f"{i}_{name}"] = {"status": "pending"}

        self._state = ProjectState(
            project_name=project_name,
            created_at=now,
            updated_at=now,
            config=config,
            input={},
            pipeline={
                "current_stage": 0,
                "stages": stages
            },
            materials={"selected": [], "generated": []},
            statistics={"total_tokens_used": 0, "total_api_calls": 0, "total_time_seconds": 0}
        )

        # Create directory structure
        (self.project_dir / "input").mkdir(parents=True, exist_ok=True)
        (self.project_dir / "stages" / "05_sections").mkdir(parents=True, exist_ok=True)
        (self.project_dir / "output" / "materials").mkdir(parents=True, exist_ok=True)
        (self.project_dir / "prompts").mkdir(parents=True, exist_ok=True)

        self.save()
        logger.info(f"Created new project: {project_name}")
        return self._state

    def update_stage(
        self,
        stage_key: str,
        status: str,
        **kwargs
    ):
        """
        Update stage status and metadata.

        Args:
            stage_key: Stage key (e.g., "2_format")
            status: New status ("pending", "in_progress", "completed", "error")
            **kwargs: Additional stage metadata
        """
        if not self._state:
            logger.error("No state loaded")
            return

        stage = self._state.pipeline["stages"].get(stage_key, {})
        stage["status"] = status

        if status == "in_progress" and not stage.get("started_at"):
            stage["started_at"] = datetime.now().isoformat()

        if status == "completed":
            stage["completed_at"] = datetime.now().isoformat()

        for key, value in kwargs.items():
            stage[key] = value

        # Update current stage
        stage_num = int(stage_key.split("_")[0])
        if status == "completed":
            self._state.pipeline["current_stage"] = stage_num

        self._state.pipeline["stages"][stage_key] = stage
        self.save()
        logger.info(f"Updated stage {stage_key}: {status}")

    def get_stage_status(self, stage_key: str) -> Optional[str]:
        """
        Get stage status.

        Args:
            stage_key: Stage key

        Returns:
            Status string or None
        """
        if not self._state:
            return None
        return self._state.pipeline["stages"].get(stage_key, {}).get("status")

    def get_last_completed_stage(self) -> int:
        """
        Get number of last completed stage.

        Returns:
            Stage number (0 if none completed)
        """
        if not self._state:
            return 0
        return self._state.pipeline.get("current_stage", 0)

    def can_run_stage(self, stage_num: int) -> bool:
        """
        Check if stage can be run.

        Args:
            stage_num: Stage number (1-10)

        Returns:
            True if stage can run
        """
        if stage_num == 1:
            return True
        return self.get_last_completed_stage() >= stage_num - 1

    def update_statistics(self, **kwargs):
        """
        Update project statistics.

        Args:
            **kwargs: Statistics to update
        """
        if not self._state:
            return

        for key, value in kwargs.items():
            if key in self._state.statistics:
                # Accumulate numeric values
                if isinstance(value, (int, float)):
                    self._state.statistics[key] += value
                else:
                    self._state.statistics[key] = value
            else:
                self._state.statistics[key] = value

        self.save()

    def add_selected_material(self, material_id: str):
        """
        Add material to selected list.

        Args:
            material_id: Material type ID
        """
        if not self._state:
            return

        if material_id not in self._state.materials["selected"]:
            self._state.materials["selected"].append(material_id)
            self.save()
            logger.info(f"Added selected material: {material_id}")

    def add_generated_material(self, material_id: str, file_path: str):
        """
        Add generated material to list.

        Args:
            material_id: Material type ID
            file_path: Path to generated file
        """
        if not self._state:
            return

        self._state.materials["generated"].append({
            "id": material_id,
            "file": file_path,
            "generated_at": datetime.now().isoformat()
        })
        self.save()
        logger.info(f"Added generated material: {material_id} -> {file_path}")

    @property
    def state(self) -> Optional[ProjectState]:
        """Get current state."""
        return self._state

    def get(self, path: str, default: Any = None) -> Any:
        """
        Get value from state by dot-separated path.

        Args:
            path: Dot-separated path (e.g., "pipeline.current_stage")
            default: Default value if not found

        Returns:
            Value or default
        """
        if not self._state:
            return default

        obj = self._state.model_dump()
        for key in path.split('.'):
            if isinstance(obj, dict) and key in obj:
                obj = obj[key]
            else:
                return default
        return obj

    def set(self, path: str, value: Any):
        """
        Set value in state by dot-separated path.

        Args:
            path: Dot-separated path
            value: Value to set
        """
        if not self._state:
            return

        # Navigate to parent
        obj = self._state.model_dump()
        keys = path.split('.')
        parent = obj

        for key in keys[:-1]:
            if key not in parent:
                parent[key] = {}
            parent = parent[key]

        # Set value
        parent[keys[-1]] = value

        # Rebuild state
        self._state = ProjectState(**obj)
        self.save()
