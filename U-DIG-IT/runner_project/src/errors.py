"""Custom exceptions for the runner project."""

from typing import Optional


class RunnerError(Exception):
    """Base class for runner errors."""


class ConfigurationError(RunnerError):
    """Raised when configuration is invalid."""


class ValidationError(RunnerError):
    """Raised when user input fails validation."""


class CommandError(RunnerError):
    """Raised when command execution fails."""

    def __init__(self, message: str, return_code: Optional[int] = None):
        super().__init__(message)
        self.return_code = return_code


class GitError(RunnerError):
    """Raised when a git action fails."""

    def __init__(self, message: str, action: Optional[str] = None):
        super().__init__(message)
        self.action = action


class TaskError(RunnerError):
    """Raised when task processing fails."""


class KnowledgeError(RunnerError):
    """Raised when the knowledge subsystem encounters an error."""


class DecisionError(RunnerError):
    """Raised when the decision engine fails to provide guidance."""


class EthicsError(RunnerError):
    """Raised when an action violates an ethics constraint."""


class CursorError(RunnerError):
    """Raised when Cursor CLI integration fails."""


class NotReadyError(RunnerError):
    """Raised for components that are not implemented yet."""
