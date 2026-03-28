# Quickstart Overlay

This directory contains the minimal repo-owned overlay surface for the pinned CN Quickstart LocalNet foundation.

Active assets in this prompt:

- `upstream-pin.env`: pinned upstream CN Quickstart source, commit, and version metadata consumed by the bootstrap and smoke scripts
- `profiles/faithful.env.local`: `.env.local` template that preserves upstream `configureProfiles` defaults
- `profiles/lean.env.local`: `.env.local` template for lighter local preflight while preserving the upstream OAuth2 path

Design rules:

- keep the upstream `quickstart/` tree unchanged and detached at a pinned commit
- express repo-owned behavior through `.env.local` overlays and adjacent scripts first
- defer any compose override, DAR deployment, seed-data load, or asset-adapter hook until the version bridge between this repo and upstream Quickstart is pinned explicitly

The current overlay does not yet mount the Control Plane DAR into the Quickstart runtime. That step is deferred intentionally and documented in the LocalNet and asset-adapter plans.
