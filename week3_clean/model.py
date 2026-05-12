from sklearn.ensemble import GradientBoostingRegressor
from sklearn.pipeline import Pipeline

def build_model():
    """GBT Huber alpha=0.95 sub=0.65 leaf=3: smaller leaves allow finer splits"""
    return Pipeline([("model", GradientBoostingRegressor(
        n_estimators=600, max_depth=3, learning_rate=0.01,
        subsample=0.65, min_samples_leaf=3, loss="huber", alpha=0.95,
        random_state=42
    ))])
