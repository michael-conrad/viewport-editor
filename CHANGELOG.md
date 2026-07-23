# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.5.0] - 2026-07-23

### Fixed

- **File Permission Preservation** — Fixed atomic write operations to preserve original file permissions (executable bit, group/other bits) instead of using default umask-based permissions. Added `_copy_permissions` helper that copies `st_mode & 0o777` from source to destination before `os.replace`.

## [Unreleased]
