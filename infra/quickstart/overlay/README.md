# Quickstart Overlay

This directory contains the minimal repo-owned overlay surface for the pinned CN Quickstart LocalNet foundation.

Active assets in this prompt:

- `upstream-pin.env`: pinned upstream CN Quickstart source, commit, and version metadata consumed by the bootstrap and smoke scripts
- `profiles/faithful.env.local`: `.env.local` template that preserves upstream `configureProfiles` defaults
- `profiles/lean.env.local`: `.env.local` template for lighter local preflight while preserving the upstream OAuth2 path

Design rules:

- keep the upstream `quickstart/` tree unchanged and detached at a pinned commit
- express repo-owned behavior through `.env.local` overlays and adjacent scripts first
- keep DAR build and deployment in repo-owned adjacent scripts rather than patching upstream Quickstart internals
- defer seed-data load and asset-adapter hooks until their interface versions are pinned explicitly

The current overlay still does not mount the Control Plane DAR directly into the Quickstart compose definition. Instead, the repo now deploys the DAR after startup through `make localnet-deploy-dar`, which preserves upstream compose files and uses the onboarding container's package-upload path.
