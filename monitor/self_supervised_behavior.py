import pandas as pd

INPUT="data/usage_sessions.csv"

def learn_patterns():

    df = pd.read_csv(INPUT)

    patterns = {}

    for cat in df["category"].unique():

        subset = df[df["category"]==cat]

        avg_duration = subset["duration_sec"].mean()

        patterns[cat]=avg_duration

    print("Learned behavior patterns")

    print(patterns)

    return patterns

if __name__=="__main__":
    learn_patterns()
