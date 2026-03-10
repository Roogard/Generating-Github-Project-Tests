import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json

import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import cross_val_score

from src.features import extract_features
from src.agents import TEST_TYPES


FEATURE_KEYS = [
    "num_params", "num_lines", "num_imports", "cyclomatic_complexity",
    "num_statements", "num_if_branches", "num_elif_branches", "num_else_branches",
    "num_for_loops", "num_while_loops", "num_try_blocks", "num_except_handlers",
    "num_with_blocks", "num_return_statements", "num_raise_statements",
    "num_assert_statements", "num_function_calls", "num_boolean_ops",
    "num_comparisons", "num_nested_functions", "num_list_comprehensions",
    "num_dict_comprehensions", "num_generators", "num_string_literals",
    "num_numeric_literals", "max_nesting_depth", "has_recursion",
    "has_default_params", "has_star_args",
]

DEFAULT_OVERLAP_DISCOUNT = 0.3
DEFAULT_THRESHOLD = 0.05
MIN_AGENTS = 2


def _features_to_vector(features):
    return [features.get(k, 0) for k in FEATURE_KEYS]


def train_model(dataset_path, model_output_path="data/model.pkl"):
    with open(dataset_path, encoding="utf-8") as f:
        dataset = json.load(f)

    if len(dataset) < 5:
        print(f"Warning: only {len(dataset)} records, model may be unreliable")

    # build feature matrix
    X = np.array([_features_to_vector(r["features"]) for r in dataset])

    # train one regressor per agent predicting kill rate
    regressors = {}
    for tt in TEST_TYPES:
        # target: kill_rate = len(kill_vector) / total_mutants
        y = np.array([
            len(r["kill_vectors"].get(tt, [])) / max(r["total_mutants"], 1)
            for r in dataset
        ])

        # check if there's any variance
        if np.std(y) < 1e-6:
            print(f"  {tt}: no variance in kill rates (all {y[0]:.3f}), using constant")
            regressors[tt] = {"constant": float(y[0])}
            continue

        reg = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=3,
            random_state=42,
        )

        # cross validation
        n_folds = min(5, len(dataset))
        if n_folds >= 2:
            scores = cross_val_score(reg, X, y, cv=n_folds, scoring="r2")
            print(f"  {tt}: CV R² = {scores.mean():.3f} (+/- {scores.std():.3f})")
        else:
            print(f"  {tt}: too few samples for cross-validation")

        reg.fit(X, y)
        regressors[tt] = reg

    os.makedirs(os.path.dirname(model_output_path), exist_ok=True)
    joblib.dump({
        "regressors": regressors,
        "feature_keys": FEATURE_KEYS,
    }, model_output_path)
    print(f"\nModel saved to {model_output_path}")
    return regressors


def predict_agents(fn, model_path="data/model.pkl", threshold=DEFAULT_THRESHOLD,
                   overlap_discount=DEFAULT_OVERLAP_DISCOUNT):
    data = joblib.load(model_path)
    regressors = data["regressors"]

    features = extract_features(fn)
    vec = np.array([_features_to_vector(features)])

    # predict kill rate for each agent
    kill_rates = {}
    for tt in TEST_TYPES:
        model = regressors.get(tt)
        if model is None:
            kill_rates[tt] = 0.0
        elif isinstance(model, dict) and "constant" in model:
            kill_rates[tt] = model["constant"]
        else:
            pred = model.predict(vec)[0]
            kill_rates[tt] = max(0.0, min(1.0, pred))  # clamp to [0, 1]

    # greedy set cover: pick agents by kill rate with diminishing returns
    ranked = sorted(kill_rates.items(), key=lambda x: x[1], reverse=True)
    selected = []

    for tt, rate in ranked:
        marginal_gain = rate * (1.0 - overlap_discount * len(selected))
        if marginal_gain < threshold and len(selected) >= MIN_AGENTS:
            break
        selected.append(tt)

    # guarantee minimum agents
    if len(selected) < MIN_AGENTS:
        for tt, _ in ranked:
            if tt not in selected:
                selected.append(tt)
            if len(selected) >= MIN_AGENTS:
                break

    return selected


def report_importance(model_path="data/model.pkl"):
    data = joblib.load(model_path)
    regressors = data["regressors"]
    feature_keys = data["feature_keys"]

    for tt in TEST_TYPES:
        model = regressors.get(tt)
        if model is None or isinstance(model, dict):
            print(f"\n{tt}: no trained model (constant prediction)")
            continue

        importances = model.feature_importances_
        indices = np.argsort(importances)[::-1]

        print(f"\n{tt} — top 10 features:")
        for rank in range(min(10, len(indices))):
            idx = indices[rank]
            print(f"  {rank+1}. {feature_keys[idx]}: {importances[idx]:.4f}")


if __name__ == "__main__":
    args = sys.argv[1:]

    dataset_path = "data/dataset.json"
    model_output = "data/model.pkl"
    do_report = False

    i = 0
    while i < len(args):
        if args[i] == "--dataset" and i + 1 < len(args):
            dataset_path = args[i + 1]
            i += 2
        elif args[i] == "--output" and i + 1 < len(args):
            model_output = args[i + 1]
            i += 2
        elif args[i] == "--report":
            do_report = True
            i += 1
        else:
            i += 1

    if do_report:
        report_importance(model_output)
    else:
        print("Training model...")
        train_model(dataset_path, model_output)
        print("\nFeature importance report:")
        report_importance(model_output)
