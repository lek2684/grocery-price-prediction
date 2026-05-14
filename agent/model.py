from sklearn.ensemble import GradientBoostingRegressor
from sklearn.pipeline import Pipeline

def build_model():
    return Pipeline([("model", GradientBoostingRegressor(
        n_estimators=600, max_depth=3, learning_rate=0.01,
        subsample=0.65, loss="huber", alpha=0.92,
        random_state=42
    ))])
