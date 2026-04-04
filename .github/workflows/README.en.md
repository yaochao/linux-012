# `.github/workflows/`

[中文 README](./README.md)

This directory stores the GitHub Actions workflows. It now includes both continuous integration and GitHub Release asset publication workflows.

## Current File

- `ci.yml`
  continuous integration workflow covering tests, build, and `ls` boot verification
- `release.yml`
  release workflow that rebuilds images from source and uploads them to GitHub Release on a tag push or manual dispatch, with optional `source_ref` support for manual republish runs
