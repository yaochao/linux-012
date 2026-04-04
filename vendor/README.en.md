# `vendor/`

[中文 README](./README.md)

`vendor/` stores third-party source inputs only. It does not store third-party runtime images. At the moment this directory mainly holds the upstream Linux 0.12 source archive used by the `rebuild/` pipeline.

Material kept here is not relicensed by the root `LICENSE`. The repository-level boundary is documented in [THIRD_PARTY.en.md](../THIRD_PARTY.en.md).

## Main Contents

- `src/`
  location for third-party source archives

## Current Boundary

- third-party source archives are allowed under `vendor/src/`
- third-party runtime images are not allowed in the repository
- runtime images must be produced locally from this repo's own source, patches, and manifests
