# PROVENANCE — the vendored core

Donor: `https://github.com/MaverickHQ/prop-challenge-lab` at commit `cfc5af873b8d88ac2309a9232a2b3458679017a0`, vendored 2026-09-10 by
`tools/vendor_core.py`. **Unchanged except two mechanical rules** the script
applies and `occams/core/PROVENANCE.json` records:

- **R1** import paths `occams.X` → `occams.core.X`, for the vendored set only.
- **R2** `ROOT = Path(__file__).resolve().parent.parent` gains one `.parent`,
  because the files sit one directory deeper than in the donor.
- **R3** tests only: string literals `'occams.X.'` → `'occams.core.X.'`, because the
  audit ledger names functions by their real module path.

Twelve modules, not eleven: `execution` is imported by `estimators` and F1's
closure record omitted it (status log, 2026-09-10). Eleven test files come
across whole. Not taken: `test_execution` and `test_prepublish` (each imports
donor modules outside the set) and `test_archive_config` (it tests the donor's
AWS template and repository layout). One case in `test_archive` asserts the
donor's pyarrow dependency and is deselected by name in `pyproject.toml`.

`tests/test_provenance.py` asserts every vendored sha256 below on each CI run.
`python tools/vendor_core.py --verify-donor` re-derives both columns from the
donor when it is present locally.

| kind | file | LOC | donor sha256 | vendored sha256 | transformed |
|---|---|---|---|---|---|
| module | `occams/core/stats.py` | 400 | `38a48cf596c148bb…` | `054ed60f59129ce2…` | yes |
| module | `occams/core/estimators.py` | 211 | `e56cddac80e73bea…` | `8ca2d37e16e4d9cc…` | yes |
| module | `occams/core/power.py` | 177 | `fcd54566022fc704…` | `fcd54566022fc704…` | no |
| module | `occams/core/calibration.py` | 308 | `b61cbcd45686bb97…` | `e16765b128e6d70d…` | yes |
| module | `occams/core/result.py` | 169 | `73078c1f4b383e41…` | `73078c1f4b383e41…` | no |
| module | `occams/core/archive.py` | 447 | `db76b971b4d392d3…` | `c6924c57859d24e0…` | yes |
| module | `occams/core/audit.py` | 129 | `90f403d76c001f41…` | `d3e8db41a2131c5e…` | yes |
| module | `occams/core/experiment.py` | 203 | `2ff09a20c4c51369…` | `117c20d0f150eaf5…` | yes |
| module | `occams/core/backfill.py` | 158 | `1eeac37d1c4612eb…` | `1eeac37d1c4612eb…` | no |
| module | `occams/core/privacy.py` | 78 | `5c61c4d2859bbe60…` | `5c61c4d2859bbe60…` | no |
| module | `occams/core/charset.py` | 132 | `5972ece17b303b03…` | `5972ece17b303b03…` | no |
| module | `occams/core/execution.py` | 202 | `60f25f55bf87db8d…` | `60f25f55bf87db8d…` | no |
| test | `tests/core/test_stats.py` | 280 | `b7172abceb4ae0d1…` | `509c2e5c2dc1a5f5…` | yes |
| test | `tests/core/test_estimators.py` | 246 | `920b7d1c51a8523d…` | `27a7b8cdb5a6fb61…` | yes |
| test | `tests/core/test_power.py` | 134 | `48bfa98801f2941f…` | `3866ce6e6ce34b77…` | yes |
| test | `tests/core/test_calibration.py` | 156 | `6ec7c6317de35302…` | `1a4cccef975e766d…` | yes |
| test | `tests/core/test_archive.py` | 152 | `b66a10ae3b95f21d…` | `b3f2377d84934c6d…` | yes |
| test | `tests/core/test_backfill.py` | 88 | `69e3953c0bbd79d3…` | `2af4ed566945b0e6…` | yes |
| test | `tests/core/test_experiment_sop.py` | 68 | `c81515373c1b6aba…` | `6331eaf3f1bf8e96…` | yes |
| test | `tests/core/test_result.py` | 206 | `039b5fbdfd4328e6…` | `caf88e9b160346e4…` | yes |
| test | `tests/core/test_charset.py` | 79 | `fb39649deabf9abd…` | `6401fec31ea3e7c6…` | yes |
| test | `tests/core/test_privacy.py` | 29 | `f33c1d170336f419…` | `dfbfa1afac1c9bcd…` | yes |
| test | `tests/core/test_block_bootstrap.py` | 137 | `3ba68bc5ec7fabfe…` | `77e7713e6cfaf3e6…` | yes |

Module LOC total: 2614.
Full hashes are in `occams/core/PROVENANCE.json`.
