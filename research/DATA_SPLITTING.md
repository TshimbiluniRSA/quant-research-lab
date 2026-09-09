# Data-splitting policy

The calendar ranges remain unset until the chosen provider's coverage and data quality are
verified. Assign every observation one role before strategy iteration begins.

## Research/training data

Use this partition freely for exploratory analysis, hypothesis development, implementation,
and initial parameter choices. Findings made here are hypotheses, not confirmation.

## Validation data

Use this partition to compare a limited number of documented strategy versions and to test
robustness. Every access is another opportunity to overfit, so record what was compared and
why. Repeated validation-driven revisions eventually contaminate this partition.

## Final test data

Keep this partition sealed throughout development. Open it once only after the hypothesis,
strategy version, parameters, costs, and decision criteria are frozen. Do not tune or repair a
strategy after observing final-test results. Any later change creates a new research version,
and the old final test must be recorded as contaminated for that new version.

The final test is not part of a routine notebook run, dashboard workflow, parameter search, or
automated campaign.
