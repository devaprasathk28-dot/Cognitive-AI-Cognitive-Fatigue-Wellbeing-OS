from monitor.fatigue_score_engine import CognitiveFatigueModel

model = CognitiveFatigueModel()
result = None

# Simulate heavy coding session
for i in range(60):  # 60 iterations = heavy work
    result = model.update(
    category="Development",
    duration_sec=60,
    hour=23
)

print(result)
