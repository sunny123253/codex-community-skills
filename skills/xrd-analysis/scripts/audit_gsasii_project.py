#!/usr/bin/env python3
"""Audit a GSAS-II powder project without changing the requested GPX file."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import shutil
import tempfile
from pathlib import Path

import numpy as np


def finite_number(value):
    return float(value) if value is not None and np.isfinite(value) else None


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def audit(path: Path) -> dict:
    path = Path(path).resolve(strict=True)
    before = digest(path)
    with tempfile.TemporaryDirectory(prefix="xrd-gpx-audit-") as temp:
        temp_path = Path(temp) / path.name
        shutil.copy2(path, temp_path)
        # Imports and indexing can print messages and automatically save the GPX.
        # Keep those writes in the temporary directory and stdout as strict JSON.
        with contextlib.redirect_stdout(io.StringIO()):
            result = audit_copy(temp_path)
    if digest(path) != before:
        raise RuntimeError("source GPX changed during the audit")
    result.update(project=str(path), source_SHA256=before, source_unchanged=True)
    return result


def audit_copy(temp_path: Path) -> dict:
    from GSASII import GSASIIscriptable as G2sc
    from GSASII import GSASIImath as G2mth

    project = G2sc.G2Project(gpxfile=str(temp_path))
    histograms = project.histograms()
    if len(histograms) != 1 or not histograms[0].name.startswith("PWDR "):
        raise ValueError("this helper requires exactly one powder histogram")
    histogram = histograms[0]
    instrument = histogram.InstrumentParameters
    kind = instrument["Type"][0]
    if kind not in {"PXC", "PNC"}:
        raise ValueError(f"CW helper does not support {kind}; use the matching GSAS-II API")
    phases = [phase for phase in project.phases()
              if phase.data.get("Histograms", {}).get(histogram.name, {}).get("Use", False)]
    if not phases:
        raise ValueError("histogram has no active phases")
    if any(phase.data["General"].get("Modulated", False) for phase in phases):
        raise ValueError("this helper does not support modulated reflection layouts")
    if any(phase.data["General"].get("Type") != "nuclear"
           or phase.data["General"].get("doPawley", False)
           or phase.data["Histograms"][histogram.name].get("LeBail", False)
           for phase in phases):
        raise ValueError("quantification helper requires nuclear Rietveld phases, not Pawley/Le Bail")
    # GSAS-II stores the powder arrays under data["data"][1]; data[0]
    # contains histogram metadata such as hId and Nobs.
    raw = histogram.data["data"][1]
    if len(raw) < 6:
        raise ValueError("powder histogram does not contain observed/calculated arrays")
    arrays = np.vstack([np.asarray(np.ma.getdata(value), dtype=float) for value in raw[:6]])
    x, observed, weights, calculated, background, residual = arrays
    if not np.isfinite(x).all() or not np.all(np.diff(x) > 0):
        raise ValueError("scan axis must be finite and strictly increasing")
    mask = np.logical_or.reduce([np.ma.getmaskarray(value) for value in raw[:6]])
    limits = histogram.data["Limits"]
    lower, upper = map(float, limits[1])
    # Match GSAS-II's searchsorted range and inclusive masked_inside exclusions.
    active = np.zeros(x.size, dtype=bool)
    active[np.searchsorted(x, lower):np.searchsorted(x, upper) + 1] = True
    for low, high in limits[2:]:
        mask |= (x >= low) & (x <= high)
    active &= ~mask
    finite = bool(np.isfinite(arrays[:, active]).all())
    if not active.any() or not finite:
        raise ValueError("no usable points or nonfinite data within the refinement interval")
    if np.any(weights[active] < 0):
        raise ValueError("negative least-squares weights")
    residual_error = float(np.max(np.abs((observed - calculated - residual)[active])))
    positive_observed = bool(np.all(observed[active] > 0))
    expected_weights = (bool(np.allclose(weights[active], 1.0 / observed[active],
                                       rtol=1e-7, atol=1e-12)) if positive_observed else None)
    rvals = project.data.get("Covariance", {}).get("data", {}).get("Rvals", {})
    wss = float(np.sum(weights[active] * residual[active]**2))
    denominator = float(np.sum(weights[active] * observed[active]**2))
    if denominator <= 0:
        raise ValueError("weighted observed intensity is zero")
    rwp = float(100.0 * np.sqrt(wss / denominator))
    saved_rwp = finite_number(histogram.data["data"][0].get("wR", rvals.get("Rwp")))
    problems, review = [], []
    if residual_error > 1e-7:
        problems.append("saved residual differs from observed minus calculated")
    if saved_rwp is None or not np.isclose(rwp, saved_rwp, rtol=1e-7, atol=1e-7):
        problems.append("independent Rwp differs from the saved refinement statistic")
    parameter_audit = {
        "converged": bool(rvals["converged"]) if "converged" in rvals else None,
        "SVD0": int(rvals["SVD0"]) if "SVD0" in rvals else None,
        "free_parameters": int(rvals["Nvars"]) if "Nvars" in rvals else None,
        "max_shift_over_sigma": finite_number(rvals.get("Max shft/sig")),
        "frozen_parameters": [str(value) for value in project.get_Frozen()],
    }
    if parameter_audit["converged"] is False:
        problems.append("saved refinement is not converged")
    if parameter_audit["SVD0"]:
        problems.append("singular refinement directions (SVD0)")
    if any(value is None for value in parameter_audit.values()):
        review.append("incomplete convergence statistics")
    if parameter_audit["max_shift_over_sigma"] is not None and parameter_audit["max_shift_over_sigma"] >= 0.1:
        review.append("maximum parameter shift/sigma is at least 0.1; confirm stability")
    if parameter_audit["frozen_parameters"]:
        review.append("parameters frozen at limits; recheck and stabilize the saved model")
    wt_factor = float(histogram.data["data"][0].get("wtFactor", 1.0))
    if not np.isfinite(wt_factor) or wt_factor <= 0:
        raise ValueError("histogram wtFactor must be positive")
    dof = int(active.sum()) - (parameter_audit["free_parameters"] or 0)
    gof = None
    if (dof > 0 and rvals.get("Nobs") == int(active.sum())
            and parameter_audit["free_parameters"] is not None
            and rvals.get("RestraintSum", 0) == 0 and rvals.get("RestraintTerms", 0) == 0):
        gof = float(np.sqrt(wss * wt_factor / dof))
        if rvals.get("GOF") is not None and not np.isclose(gof, rvals["GOF"], rtol=1e-7, atol=1e-7):
            problems.append("independent GOF differs from the saved refinement statistic")
    fractions = histogram.ComputeMassFracs() if len(phases) > 1 else {phases[0].name: (1.0, None)}
    mass_fractions = {
        phase.name: {
            "weight_fraction": finite_number(fractions[phase.name][0]),
            "formal_su": finite_number(fractions[phase.name][1]),
        }
        for phase in phases
    }
    if any(item["weight_fraction"] is None or not 0 <= item["weight_fraction"] <= 1
           for item in mass_fractions.values()):
        raise ValueError("nonfinite or nonphysical normalized phase fractions")
    fraction_sum = sum(item["weight_fraction"] for item in mass_fractions.values())
    if abs(fraction_sum - 1.0) >= 1e-6:
        problems.append("active phase mass fractions do not sum to one")
    mass_terms = {phase.name: float(phase.getHAPvalues(histogram)["Scale"][0])
                  * float(phase.data["General"]["Mass"]) for phase in phases}
    mass_total = sum(mass_terms.values())
    if mass_total <= 0 or any(value < 0 for value in mass_terms.values()):
        problems.append("nonpositive mass normalization or negative phase scale")
    elif any(not np.isclose(mass_fractions[name]["weight_fraction"], value / mass_total,
                            rtol=1e-9, atol=1e-9) for name, value in mass_terms.items()):
        problems.append("GSAS-II mass fractions differ from scale-times-cell-mass normalization")
    profile = {}
    if kind in {"PXC", "PNC"}:
        scan = np.linspace(lower, upper, 20001)
        values = {key: value[1] for key, value in instrument.items()}
        gaussian = G2mth.getCWsig(values, scan)
        lorentzian = G2mth.getCWgam(values, scan)
        profile = {
            "instrument_type": kind,
            "sampled_grid_points": int(scan.size),
            "gaussian_variance_min": float(gaussian.min()),
            "gaussian_variance_negative_points": int(np.sum(gaussian < 0.0)),
            "lorentzian_fwhm_min": float(lorentzian.min()),
            "lorentzian_fwhm_negative_points": int(np.sum(lorentzian < 0.0)),
            "scope": "instrument contributions, not the total width including sample broadening",
        }
        if (profile["gaussian_variance_negative_points"]
                or profile["lorentzian_fwhm_negative_points"]):
            review.append("negative instrument peak-width contribution; check total width before clipping")
    orientation = {}
    for name, values in histogram.data.get("Reflection Lists", {}).items():
        reflections = np.asarray(values.get("RefList", []), dtype=float)
        if reflections.ndim == 2 and reflections.shape[1] > 12 and reflections.shape[0]:
            corrections = reflections[:, 12]
            orientation[name] = {
                "minimum": float(corrections.min()),
                "maximum": float(corrections.max()),
                "negative_count": int(np.sum(corrections < 0.0)),
                "nonpositive_count": int(np.sum(corrections <= 0.0)),
                "saved_gaussian_at_floor_count": int(np.sum(reflections[:, 6] <= 0.001 + 1e-12)),
                "saved_lorentzian_at_floor_count": int(np.sum(reflections[:, 7] <= 0.001 + 1e-12)),
            }
            if not np.isfinite(reflections[:, [6, 7, 12]]).all():
                problems.append(f"{name}: nonfinite reflection widths or orientation corrections")
            if orientation[name]["nonpositive_count"]:
                problems.append(f"{name}: nonpositive preferred-orientation reflection corrections")
            if np.any(reflections[:, 6:8] <= 0):
                problems.append(f"{name}: nonpositive saved reflection width")
            if (orientation[name]["saved_gaussian_at_floor_count"]
                    or orientation[name]["saved_lorentzian_at_floor_count"]):
                review.append(f"{name}: saved width at GSAS-II floor; inspect the unclipped total")
    if any(phase.name not in orientation for phase in phases):
        review.append("missing reflection diagnostics for an active phase")
    return {
        "scope": "single-histogram nonmodulated CW powder model; numerical screening only",
        "status": "issues_found" if problems else ("review_required" if review else "no_detected_numerical_issues"),
        "problems": problems,
        "review_required": review,
        "limitations": ["phase completeness and absolute composition are not certified",
                        "only saved reflections are checked for texture; perform the direction-grid audit separately"],
        "histogram": histogram.name,
        "points": int(x.size),
        "fitted_points": int(active.sum()),
        "masked_points": int(mask.sum()),
        "fit_limits_deg": [lower, upper],
        "excluded_intervals_deg": [[float(low), float(high)] for low, high in limits[2:]],
        "two_theta_range_deg": [float(x.min()), float(x.max())],
        "data_consistency": {
            "finite": finite,
            "observed_positive": positive_observed,
            "weights_equal_one_over_observed": expected_weights,
            "max_residual_identity_error": residual_error,
            "independent_Rwp_percent": rwp,
            "saved_Rwp_percent": saved_rwp,
            "independent_GOF": gof,
            "histogram_weight_factor": wt_factor,
        },
        "refinement": parameter_audit,
        "mass_fractions": mass_fractions,
        "mass_fraction_sum": fraction_sum,
        "mass_fractions_normalized_to_active_phases": bool(abs(fraction_sum - 1.0) < 1e-6),
        "formal_su_is_accuracy": False,
        "profile": profile,
        "preferred_orientation_reflection_corrections": orientation,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("gpx", type=Path, help="path to a GSAS-II .gpx project")
    parser.add_argument("--output", type=Path, help="JSON output; defaults to stdout")
    args = parser.parse_args()
    if not args.gpx.is_file():
        parser.error(f"GPX not found: {args.gpx}")
    if args.output and args.output.exists():
        parser.error(f"refusing to overwrite existing output: {args.output}")
    result = audit(args.gpx)
    text = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as stream:
            stream.write(text + "\n")
    else:
        print(text)


if __name__ == "__main__":
    main()
