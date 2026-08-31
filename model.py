import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
import joblib

# Load dataset
df = pd.read_csv("last_copy.csv")

# Filter rows with density < 0.55
df = df[df["density"] < 0.55]

# Encode lane_id
le = LabelEncoder()
df["lane_id_encoded"] = le.fit_transform(df["lane_id"])
joblib.dump(le, "lane_encoder.pkl")

# Add interaction features
df["net_flow"] = df["entering_rate"] - df["exit_rate"]
df["flow_ratio"] = df["entering_rate"] / (df["exit_rate"] + 1)
df["flow_vs_count"] = df["net_flow"] / (df["vehicle_count"] + 1)

# Select features and target
features = [
    "lane_id_encoded", "density", "entering_rate", "exit_rate", "vehicle_count",
    "net_flow", "flow_ratio", "flow_vs_count"
]
X = df[features]
y = df["congested"]

# Scale numeric features
scaler = StandardScaler()
numeric_cols = ["density", "entering_rate", "exit_rate", "vehicle_count", "net_flow", "flow_ratio", "flow_vs_count"]
X_scaled = X.copy()
X_scaled[numeric_cols] = scaler.fit_transform(X[numeric_cols])
joblib.dump(scaler, "scaler.pkl")

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

# Train the model
clf = GradientBoostingClassifier(n_estimators=100, max_depth=5, random_state=42)
clf.fit(X_train, y_train)
joblib.dump(clf, "congestion_predictor.pkl")

# Evaluate
print("✅ Model trained and saved with new interaction features.")
print("🎯 Accuracy on test set:", clf.score(X_test, y_test))
print("📊 Congestion ratio (after filter):\n", df['congested'].value_counts(normalize=True))
