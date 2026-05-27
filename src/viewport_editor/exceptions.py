# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""Domain exceptions for viewport-editor actions.

Co-authored with AI: OpenCode (deepseek-v4-flash)
"""


class ViewportError(Exception):
    """Base exception for viewport-editor errors. Signals isError=true in MCP response."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class JumpTargetNotFoundError(ViewportError):
    """Raised when viewport:jump target is not found in the file."""

    def __init__(self, target: str) -> None:
        super().__init__(f"Target not found: {target}")


class JumpLineOutOfRangeError(ViewportError):
    """Raised when viewport:jump target line is out of range."""

    def __init__(self, line_num: int, total: int) -> None:
        super().__init__(f"Target line {line_num} out of range (1-{total})")


class ViewportNotFoundError(ViewportError):
    """Raised when a viewport_id does not exist in the session."""

    def __init__(self, viewport_id: str) -> None:
        super().__init__(f"Viewport not found: {viewport_id}")


class SessionNotFoundError(ViewportError):
    """Raised when a session_id does not exist."""

    def __init__(self, session_id: str) -> None:
        super().__init__(f"Session not found: {session_id}")


class FileNotFoundError_(ViewportError):
    """Raised when a file path does not exist on disk."""

    def __init__(self, file_path: str) -> None:
        super().__init__(f"File not found: {file_path}")


class PathEscapeError(ViewportError):
    """Raised when a file path escapes the project root."""

    def __init__(self, file_path: str) -> None:
        super().__init__(f"Path escapes project root: {file_path}")


class AbsolutePathError(ViewportError):
    """Raised when an absolute path is provided."""

    def __init__(self, file_path: str) -> None:
        super().__init__(f"Absolute paths not allowed: {file_path}")


class InvalidDisplayModeError(ViewportError):
    """Raised when display_mode is not 'hide' or 'show'."""

    def __init__(self, mode: str) -> None:
        super().__init__(f"display_mode must be 'hide' or 'show', got {mode!r}")


class EditTargetNotFoundError(ViewportError):
    """Raised when edit old_text not found in buffer."""

    def __init__(self, target: str) -> None:
        super().__init__(f"Edit target not found: {target}")


class LineRangeError(ViewportError):
    """Raised when line range is invalid."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
