"""System diagnostics and health checks."""

from dataclasses import dataclass
from typing import Optional
import sys
import os
import shutil
import logging

logger = logging.getLogger(__name__)


@dataclass
class CheckResult:
    """Result of a diagnostic check."""
    name: str
    passed: bool
    message: str
    details: Optional[str] = None


class Diagnostics:
    """System diagnostics and health checks."""

    def __init__(self, config: dict):
        """
        Initialize diagnostics.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.results: list[CheckResult] = []

    def run_all(self) -> list[CheckResult]:
        """
        Run all diagnostic checks.

        Returns:
            List of check results
        """
        self.results = []

        self.check_python_version()
        self.check_api_key()
        self.check_api_connection()
        self.check_available_models()
        self.check_directories()
        self.check_dependencies()
        self.check_external_editor()
        self.check_terminal_capabilities()

        return self.results

    def check_python_version(self):
        """Check Python version."""
        version = sys.version_info
        passed = version >= (3, 11)
        self.results.append(CheckResult(
            name="Python version",
            passed=passed,
            message=f"{version.major}.{version.minor}.{version.micro}",
            details="Requires Python 3.11+" if not passed else None
        ))

    def check_api_key(self):
        """Check if Gemini API key is set."""
        api_key = os.environ.get("GEMINI_API_KEY", "")
        passed = len(api_key) > 0
        self.results.append(CheckResult(
            name="Gemini API key",
            passed=passed,
            message="Set" if passed else "Not found",
            details="Set GEMINI_API_KEY environment variable" if not passed else None
        ))

    def check_api_connection(self):
        """Check connection to Gemini API."""
        import time

        try:
            start = time.time()
            import google.generativeai as genai

            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                self.results.append(CheckResult(
                    name="Gemini API connection",
                    passed=False,
                    message="Skipped (no API key)"
                ))
                return

            genai.configure(api_key=api_key)
            list(genai.list_models())
            elapsed = int((time.time() - start) * 1000)

            self.results.append(CheckResult(
                name="Gemini API connection",
                passed=True,
                message=f"OK ({elapsed}ms)"
            ))

        except Exception as e:
            self.results.append(CheckResult(
                name="Gemini API connection",
                passed=False,
                message="Failed",
                details=str(e)
            ))

    def check_available_models(self):
        """Check available Gemini models."""
        try:
            import google.generativeai as genai

            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                self.results.append(CheckResult(
                    name="Available models",
                    passed=False,
                    message="Skipped (no API key)"
                ))
                return

            genai.configure(api_key=api_key)
            models = [
                m for m in genai.list_models()
                if "generateContent" in m.supported_generation_methods
            ]
            count = len(models)

            self.results.append(CheckResult(
                name="Available models",
                passed=count > 0,
                message=f"{count} models found"
            ))

        except Exception as e:
            self.results.append(CheckResult(
                name="Available models",
                passed=False,
                message="Error",
                details=str(e)
            ))

    def check_directories(self):
        """Check required directories."""
        projects_dir = self.config.get("projects_dir", "./projects")
        prompts_dir = self.config.get("prompts_dir", "./prompts")

        # Check projects directory
        try:
            os.makedirs(projects_dir, exist_ok=True)
            test_file = os.path.join(projects_dir, ".write_test")
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)

            self.results.append(CheckResult(
                name="Projects directory",
                passed=True,
                message=f"{projects_dir} (writable)"
            ))
        except Exception as e:
            self.results.append(CheckResult(
                name="Projects directory",
                passed=False,
                message=projects_dir,
                details=f"No write access: {e}"
            ))

        # Check prompts directory
        exists = os.path.isdir(prompts_dir)
        self.results.append(CheckResult(
            name="Prompts directory",
            passed=exists,
            message=f"{prompts_dir} ({'exists' if exists else 'not found'})",
            details="Will be created when needed" if not exists else None
        ))

    def check_dependencies(self):
        """Check required Python packages."""
        required = [
            ("google.generativeai", "google-generativeai"),
            ("textual", "textual"),
            ("rich", "rich"),
            ("docx", "python-docx"),
            ("yaml", "pyyaml"),
            ("click", "click"),
            ("pydantic", "pydantic"),
        ]

        missing = []
        for module, package in required:
            try:
                __import__(module.split(".")[0])
            except ImportError:
                missing.append(package)

        passed = len(missing) == 0
        self.results.append(CheckResult(
            name="Dependencies",
            passed=passed,
            message="All installed" if passed else f"Missing: {', '.join(missing)}",
            details=f"Install with: pip install {' '.join(missing)}" if missing else None
        ))

    def check_external_editor(self):
        """Check external editor configuration."""
        editor = os.environ.get("EDITOR", "")
        if editor:
            exists = shutil.which(editor) is not None
            self.results.append(CheckResult(
                name="External editor",
                passed=exists,
                message=editor if exists else f"{editor} (not found)",
                details="Editor not in PATH" if not exists else None
            ))
        else:
            self.results.append(CheckResult(
                name="External editor",
                passed=False,
                message="Not set ($EDITOR)",
                details="Optional: set EDITOR environment variable"
            ))

    def check_terminal_capabilities(self):
        """Check terminal capabilities."""
        # Unicode
        try:
            # Try to print Unicode
            import io
            import contextlib

            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                print("тест")
            unicode_ok = True
        except:
            unicode_ok = False

        self.results.append(CheckResult(
            name="Terminal Unicode",
            passed=unicode_ok,
            message="Supported" if unicode_ok else "Not supported"
        ))

        # Colors
        colors = os.environ.get("COLORTERM", "")
        term = os.environ.get("TERM", "")

        if colors in ("truecolor", "24bit"):
            color_msg = "True Color (16M colors)"
        elif "256" in term:
            color_msg = "256 colors"
        else:
            color_msg = "Basic colors"

        self.results.append(CheckResult(
            name="Terminal colors",
            passed=True,
            message=color_msg
        ))
