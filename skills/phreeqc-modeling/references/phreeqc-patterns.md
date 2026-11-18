# PHREEQC Modeling Patterns

## Static Reaction File Layout

Recommended order:

1. `TITLE`
2. assumptions and database comments
3. `RATES`
4. `KNOBS`
5. initial `SOLUTION`
6. initial gas/equilibrium setup
7. `SELECTED_OUTPUT`
8. `USER_PUNCH`
9. reaction scenarios
10. post-processing scenarios

## Mass Loss Output

For mineral moles remaining in `KINETICS`, compute rock mass loss with molecular weights:

```phreeqc
USER_PUNCH 1
    -headings day rock_loss_g rock_loss_pct calcite_precip_g net_loss_g
    -start
    10 PUNCH TOTAL_TIME / 86400
    20 loss_g = (0.51236 - KIN("Calcite_kin")) * 100.0869
    30 precip_g = EQUI("Calcite") * 100.0869
    40 PUNCH loss_g
    50 PUNCH loss_g / 51.28 * 100
    60 PUNCH precip_g
    70 PUNCH loss_g - precip_g
    -end
```

For staged simulations where a degassing step has no `KINETICS`, pass the prior stage's rock loss with `PUT/GET`:

```phreeqc
USER_PUNCH 1
    -start
    10 IF SIM_NO = 2 THEN loss_g = (0.51236 - KIN("Calcite_kin")) * 100.0869
    20 IF SIM_NO = 2 THEN PUT(loss_g, 2)
    30 IF SIM_NO = 4 THEN loss_g = GET(2)
    40 precip_g = EQUI("Calcite") * 100.0869
    50 PUNCH loss_g, precip_g, loss_g - precip_g
    -end
```

## Arrhenius Correction

Use:

```text
k_T = k_25 * exp[-Ea/R * (1/T - 1/298.15)]
k_25 = 10^logk25
R = 8.314462618 J/mol/K
```

Example values at 323.15 K:

| Mineral | logk25 | Ea kJ/mol | k50 mol/m2/s |
|---|---:|---:|---:|
| Quartz | -13.89 | 87.70 | 1.9890e-13 |
| Calcite | -8.81 | 23.50 | 3.2248e-09 |
| Dolomite | -7.53 | 52.20 | 1.5048e-07 |

## Degassing Precipitation Pattern

Use this when the experiment shows mass loss during high-pressure reaction but visible carbonate precipitates after removing the sample:

```phreeqc
# high pressure reaction
USE solution 10
EQUILIBRIUM_PHASES 21
    CO2(g) 2.170 10
KINETICS 21 high_pressure_reaction
    Calcite_kin
        -formula Calcite 1
        -m0 0.51236
        -m  0.51236
        -parms 12.82 0.67 3.2248e-09
    -steps 259200 seconds
SAVE solution 21
END

# post-removal degassing
USE solution 21
EQUILIBRIUM_PHASES 31
    CO2(g) -3.377 0
    Calcite 0 0
SAVE solution 31
END
```

Report rock dissolution and secondary precipitation separately. Only subtract them when the precipitate remains attached to the specimen and the experimental weighing includes it.

## Common Pitfalls

- `RATES` names must match `KINETICS` names.
- Relative `SELECTED_OUTPUT -file` paths are written relative to the current working directory, not necessarily the input file's directory.
- `EQUI("Phase")` is only meaningful in simulations that include the phase in `EQUILIBRIUM_PHASES`.
- `KIN("Reactant")` is not available in a later pure equilibrium stage unless passed with `PUT/GET` or recomputed another way.
- Adding `Calcite 0 0` during the high-pressure stage can suppress kinetic calcite dissolution if used incorrectly. Prefer allowing secondary calcite in a separate degassing stage unless the experiment requires in-situ precipitation.
- The phase amount shown for `CO2(g)` in `EQUILIBRIUM_PHASES` is a boundary reservoir, not a measured gas tank unless explicitly modeled as finite.
