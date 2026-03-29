# Return Demo Scenario

This directory contains the manifest, policy, inventory snapshot, and obligation inputs for the confidential collateral return and release prototype.

Current contents:

- `return-policy.json` for the demo-specific policy variant with conservative control requirements
- `positive-inventory.json` for the currently encumbered collateral set consumed by all return scenarios
- `positive-obligation.json` for the successful return path with deterministic retained coverage
- `negative-unauthorized-obligation.json` for the unauthorized release control failure
- `negative-replay-obligation.json` for the replay-protection path
- `negative-mismatch-obligation.json` for the stale obligation-state mismatch path
- `demo-config.json` for the manifest consumed by `make demo-return`
