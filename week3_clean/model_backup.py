from sklearn.ensemble import GradientBoostingRegressor
from sklearn.pipeline import Pipeline

def build_model():
    """Axis: n_estimators. Changed: 800->600. Fixed: depth=3, lr=0.01, sub=0.6"""
    return Pipeline([("model", GradientBoostingRegressor(
        n_estimators=600, max_depth=3, learning_rate=0.01,
        subsample=0.6, min_samples_leaf=5, random_state=42
    ))])
