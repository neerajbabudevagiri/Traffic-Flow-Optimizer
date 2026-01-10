from sklearn.ensemble import RandomForestClassifier
import pandas as pd

# Load your dataset
df = pd.read_csv("traffic_training_data.csv")

# Remove the first 2,500,000 rows
df = df.iloc[2600000:]

# Features (inputs) and label (output)
X = df[["density", "speed_exit", "vehicle_count"]]
y = df["congested"]

# Train-test split
from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

from sklearn.preprocessing import StandardScaler
scalar = StandardScaler()

# Train the model
clf = RandomForestClassifier(max_depth=10)
clf.fit(X_train, y_train)
print(df['congested'].value_counts(normalize=True))

# Evaluate it
print("Accuracy:", clf.score(X_test, y_test))


import joblib

# Save the model to a file
joblib.dump(clf, "congestion_predictor.pkl")

# (Optional) Save the scaler if you're using one
joblib.dump(scalar, "scaler.pkl")

