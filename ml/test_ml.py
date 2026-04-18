from recommender import get_recommender

# Load model
recommender = get_recommender(models_dir="models")

# Sample input
data = {
    "electricity_level": "high",
    "num_servers_onprem": 50,
    "renewable_energy_percent": 10
}

# Fake rule output
result = {
    "scope1": 10,
    "scope2": 70,
    "scope3": 20
}

findings = ["High electricity usage"]

# Run ML
output = recommender.recommend(result, data, findings)

print("\nML OUTPUT:\n", output)