# `.github/workflows/`

[中文 README](./README.md)

This directory stores the GitHub Actions workflows. It now includes both continuous integration and GitHub Release asset publication workflows.

## Current File

- `ci.yml`
  continuous integration workflow covering tests, build, `ls` boot verification, and a two-build reproducibility check
- `release.yml`
  release workflow that rebuilds images from source, uploads them to GitHub Release, and then reads those published assets back for another boot verification; manual republish runs also support an optional `source_ref`
