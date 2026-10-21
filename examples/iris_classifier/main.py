import argparse
import json
from pathlib import Path

from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    config = json.loads(input_path.read_text(encoding="utf-8"))
    test_size = float(config.get("test_size", 0.25))
    random_state = int(config.get("random_state", 42))

    if not 0 < test_size < 1:
        raise ValueError("test_size must be between 0 and 1")

    dataset = load_iris()
    x_train, x_test, y_train, y_test = train_test_split(
        dataset.data,
        dataset.target,
        test_size=test_size,
        random_state=random_state,
        stratify=dataset.target,
    )

    model = LogisticRegression(max_iter=500)
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)

    result = {
        "workload": "iris-classifier",
        "dataset": "Iris",
        "samples": len(dataset.data),
        "test_samples": len(y_test),
        "accuracy": float(accuracy_score(y_test, predictions)),
        "classes": dataset.target_names.tolist(),
        "status": "success",
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()