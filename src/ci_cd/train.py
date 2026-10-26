import json
import pathlib

import joblib
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.model_selection import train_test_split

MODEL_DIR = pathlib.Path("model")

# Model settings.
N_ESTIMATORS = 10  # number of trees in the forest
MAX_DEPTH = None  # maximum depth of each tree; None means no limit
RANDOM_STATE = 42  # fixed seed
TEST_SIZE = 0.2  # test split fraction


def load_data():
    """Split the iris dataset into a training set and a test set."""
    iris = load_iris()
    X_train, X_test, y_train, y_test = train_test_split(
        iris.data, iris.target, test_size=TEST_SIZE, random_state=RANDOM_STATE
    )
    return X_train, X_test, y_train, y_test


def train() -> dict:
    X_train, X_test, y_train, y_test = load_data()
    print(
        f"Training RandomForestClassifier with N_ESTIMATORS={N_ESTIMATORS} and MAX_DEPTH={MAX_DEPTH}"
    )

    clf = RandomForestClassifier(
        n_estimators=N_ESTIMATORS, max_depth=MAX_DEPTH, random_state=RANDOM_STATE
    )
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    acc = float(accuracy_score(y_test, y_pred))
    cm = confusion_matrix(y_test, y_pred).tolist()

    MODEL_DIR.mkdir(exist_ok=True)
    joblib.dump(clf, MODEL_DIR / "model.pkl")

    metrics = {
        "accuracy": acc,
        "confusion_matrix": cm,
        "classes": load_iris().target_names.tolist(),
    }
    (MODEL_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2))

    return metrics


if __name__ == "__main__":
    metrics = train()
    print(f"Accuracy: {metrics['accuracy']:.4f}")
