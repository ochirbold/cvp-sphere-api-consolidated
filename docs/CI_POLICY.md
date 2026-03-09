# CI Policy (Stage-2)

`ci-guards` is the source of truth for merge readiness.

## Required checks

1. Duplicate file guard
2. Import smoke
3. LP regression tests

## Branch protection setup (GitHub UI)

1. Open repository settings -> Branches.
2. Add branch protection rule for `main`.
3. Enable:
   - Require a pull request before merging
   - Require approvals (recommended: 1+)
   - Require status checks to pass before merging
4. Select required check: `guard-and-regression` job from `ci-guards` workflow.
5. Optionally enable: Dismiss stale approvals and Require conversation resolution.

## Fail policy

If CI fails, do not merge.
Fix or revert before re-running checks.
