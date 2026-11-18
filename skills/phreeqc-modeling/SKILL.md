---
name: phreeqc-modeling
description: Build, modify, calibrate, and verify PHREEQC geochemical models for water-rock-CO2 reactions, batch reactors, brines, kinetic mineral dissolution, equilibrium precipitation, degassing, mass-loss matching, .pqi/.phrq inputs, .sel/.out outputs, and PHREEQC database selection. Use when the user asks to reproduce geochemical experiments, translate paper methods into PHREEQC, set kinetic/surface-area parameters, simulate carbonate dissolution/precipitation, or run/check PHREEQC models.
---

# PHREEQC Modeling

## Core Workflow

1. Preserve the user's project rules first. If the task needs Python, pip, uv, pytest, notebooks, conda, venv, requirements, or environment setup, inspect the project environment files and follow the project-specific environment policy before running Python tools.
2. Read project memory before modeling when available. In this project, check `memory/` for prior PHREEQC assumptions, validated commands, and calibration notes.
3. Extract experimental constraints before editing `.pqi`: solution composition, temperature, pressure or fugacity, water mass, gas/headspace assumptions, rock mass, mineral composition, reaction time, flow/static setting, validation targets, and missing parameters.
4. Choose the database intentionally:
   - Use `pitzer.dat` for high-ionic-strength brines such as 5 wt% NaCl.
   - Use `phreeqc.dat` or `wateq4f.dat` for simpler dilute systems when Pitzer interactions are not needed.
   - Verify phase names and available elements in the selected database by running PHREEQC.
5. Build the model in separable stages:
   - Initial brine/speciation stage.
   - High-pressure/high-CO2 water-rock reaction stage.
   - Optional post-processing stages such as degassing, precipitation, flushing, or pressure changes.
6. Keep dissolution and precipitation conceptually separate. Use kinetic reactants for original rock minerals and a separate equilibrium phase or kinetic reactant for secondary precipitates.
7. Add `SELECTED_OUTPUT` and `USER_PUNCH` early. Output pH, ionic strength, totals, saturation indices, kinetic remaining moles, equilibrium phase amounts, rock mass loss, precipitate mass, and net mass change.
8. Run PHREEQC after each meaningful edit. Do not claim a model works until the `.out` has no `ERROR:` lines and expected output rows exist.

## Local PHREEQC Command Pattern

In this project, prefer the command-line PHREEQC path recorded in `README.md`:

```powershell
& "C:\Program Files\USGS\phreeqc-3.8.6-17100-x64\bin\Release\phreeqc.exe" `
  "input.pqi" `
  "output.out" `
  "C:\Program Files\USGS\phreeqc-3.8.6-17100-x64\database\pitzer.dat"
```

Run from the model directory when `SELECTED_OUTPUT -file` uses a relative path, so `.sel` files land beside the input.

## Batch CO2-Water-Rock Model Pattern

Use this structure for static reaction vessels:

```phreeqc
SOLUTION 1 initial_brine
    temp 50
    pressure 148
    units mol/kgw
    pH 7 charge
    Na 0.9006
    Cl 0.9006
    Ca 1e-12
    Mg 1e-12
    Si 1e-12
    -water 1

EQUILIBRIUM_PHASES 1
    CO2(g) 2.170 10
SAVE solution 10
END
```

For CO2 pressure conversion:

```text
p_atm = p_MPa / 0.101325
log10_p = log10(p_atm)
15 MPa -> 148 atm -> CO2(g) 2.170
atmospheric CO2 -> log10(0.00042) about -3.377
```

Use fixed `CO2(g)` for pressure-maintained experiments. Use finite `GAS_PHASE` or kinetic CO2 transfer when headspace inventory and gas-liquid transfer matter.

## Kinetic Mineral Dissolution

Translate table parameters carefully:

```text
A_total = A_beta * V_mineral * roughness_multiplier
V_mineral = mineral_mass_kg / density_kg_m3
k_T = 10^logk25 * exp[-Ea/R * (1/T - 1/298.15)]
```

Where:

- `A_beta` is area density, usually m2/m3.
- `Ea` is J/mol in the Arrhenius equation.
- `T` is Kelvin.
- `roughness_multiplier` represents rough core surfaces, fractures, exposed pores, or calibration to observed mass loss.

Use kinetic dissolution only when undersaturated:

```phreeqc
RATES
Calcite_kin
    -start
    10 IF (M <= 0) THEN GOTO 200
    20 sat = SR("Calcite")
    30 IF (sat >= 1) THEN GOTO 200
    40 area = PARM(1) * (M/M0)^PARM(2)
    50 rate = area * PARM(3) * (1 - sat)
    60 moles = rate * TIME
    70 IF (moles > M) THEN moles = M
    200 SAVE moles
    -end
```

## Degassing And Secondary Precipitation

To model white carbonate precipitates after removing samples from a high-pressure CO2 reactor, add a post-reaction stage:

```phreeqc
USE solution 21
EQUILIBRIUM_PHASES 31
    CO2(g) -3.377 0
    Calcite 0 0
SAVE solution 31
END
```

Interpretation:

- High-pressure stage: rock minerals dissolve and mass is lost.
- Degassing stage: dissolved CO2 drops, pH rises, calcite saturation may increase, and secondary calcite can precipitate.
- Net sample mass change should be tracked as `rock_loss_g - secondary_precipitate_g` only if precipitate remains attached to the specimen; otherwise report them separately.

## Calibration Rules

- Never treat calibrated effective surface area as a unique physical surface area.
- State which parameters are measured and which are calibrated.
- If raw table surface areas produce too little reaction, add an explicit roughness/fracture multiplier rather than silently changing `A_beta`.
- Calibrate against the most direct measured target first: mass loss, effluent chemistry, pH, pressure, or mineral change.
- Preserve both raw-parameter and calibrated-parameter versions when the difference matters for interpretation.

## Verification Checklist

After editing or creating a PHREEQC model:

1. Run PHREEQC with the intended database.
2. Search the `.out` for `ERROR:` and `WARNING:`.
3. Open the `.sel` and confirm rows, columns, and scenario numbering are meaningful.
4. Check units in `USER_PUNCH`; PHREEQC totals are usually mol/kgw.
5. Compare validation targets and report both model values and paper/experiment values.
6. Update project memory with model files, assumptions, database, command, and key verified results.

## References

Read `references/phreeqc-patterns.md` when you need concrete templates for:

- static CO2-water-rock reaction files;
- mass-loss and precipitate output;
- using `PUT/GET` to carry values across staged simulations;
- interpreting high-pressure reaction followed by atmospheric degassing.
