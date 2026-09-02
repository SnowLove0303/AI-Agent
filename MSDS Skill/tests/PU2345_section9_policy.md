# PU-2345 Section 9 regression baseline

The current PU-2345 semantic model contains ten Section 9 property rows whose complete value is a missing-data placeholder. Those rows are omitted as whole rows before output:

- `9.7` evaporation rate
- `9.10` saturated vapour pressure
- `9.11` relative vapour density
- `9.14` surface tension
- `9.15` log Pow / n-octanol-water partition coefficient
- `9.16` auto-ignition temperature
- `9.17` ignition temperature
- `9.18` decomposition temperature
- `9.20` explosive properties
- `9.21` dust explosion class

The surviving properties retain source order and are renumbered continuously as `9.1` through `9.13`. Actual values, `不适用` / `Not applicable`, and the substantive `其他信息` / `Other information` row remain visible. This policy is applied identically to CN/EN and Guanzhi/Guocai outputs.
