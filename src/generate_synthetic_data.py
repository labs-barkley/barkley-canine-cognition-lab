"""
Barkley Canine Cognition Lab
Synthetic DogGraph Data Generator

Generates a realistic synthetic dataset of 100 dogs over 12 months.
Includes realistic noise: sensor dropouts, missing days, outliers,
context disruptions (travel, boarding, owner absence).

This is synthetic data for research demonstration purposes only.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import os

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

# ──────────────────────────────────────────────────────────────────────────────
# BREED PROFILES
# Each breed has a population-level mean and std for behavioral signals.
# These are illustrative values — not clinically validated norms.
# ──────────────────────────────────────────────────────────────────────────────

BREED_PROFILES = {
    "Labrador Retriever": {
        "sleep_hours_mean": 12.5, "sleep_hours_std": 1.8,
        "activity_minutes_mean": 85, "activity_minutes_std": 20,
        "social_score_mean": 7.8, "social_score_std": 1.2,
        "nocturnal_restlessness_mean": 1.5, "nocturnal_restlessness_std": 0.8,
        "vocalization_mean": 3.2, "vocalization_std": 1.5,
    },
    "Border Collie": {
        "sleep_hours_mean": 11.0, "sleep_hours_std": 1.5,
        "activity_minutes_mean": 110, "activity_minutes_std": 25,
        "social_score_mean": 7.2, "social_score_std": 1.4,
        "nocturnal_restlessness_mean": 2.0, "nocturnal_restlessness_std": 1.0,
        "vocalization_mean": 4.0, "vocalization_std": 1.8,
    },
    "Golden Retriever": {
        "sleep_hours_mean": 13.0, "sleep_hours_std": 1.6,
        "activity_minutes_mean": 75, "activity_minutes_std": 18,
        "social_score_mean": 8.2, "social_score_std": 1.0,
        "nocturnal_restlessness_mean": 1.2, "nocturnal_restlessness_std": 0.7,
        "vocalization_mean": 2.8, "vocalization_std": 1.2,
    },
    "Beagle": {
        "sleep_hours_mean": 12.0, "sleep_hours_std": 2.0,
        "activity_minutes_mean": 70, "activity_minutes_std": 22,
        "social_score_mean": 6.8, "social_score_std": 1.5,
        "nocturnal_restlessness_mean": 2.5, "nocturnal_restlessness_std": 1.2,
        "vocalization_mean": 5.5, "vocalization_std": 2.0,
    },
    "French Bulldog": {
        "sleep_hours_mean": 14.0, "sleep_hours_std": 1.4,
        "activity_minutes_mean": 45, "activity_minutes_std": 15,
        "social_score_mean": 7.5, "social_score_std": 1.1,
        "nocturnal_restlessness_mean": 2.8, "nocturnal_restlessness_std": 1.3,
        "vocalization_mean": 3.0, "vocalization_std": 1.4,
    },
}

BREEDS = list(BREED_PROFILES.keys())
AGE_GROUPS = ["young_adult", "adult", "senior"]  # 1-3y, 3-8y, 8y+


def generate_individual_baseline(breed_profile, age_group, individual_offset_scale=0.15):
    """
    Each dog has its own stable baseline that differs from breed average.
    individual_offset_scale controls how much individual variation exists
    beyond the breed-level distribution.
    """
    baseline = {}
    for key, val in breed_profile.items():
        if key.endswith("_mean"):
            signal = key.replace("_mean", "")
            std = breed_profile[f"{signal}_std"]
            # Individual baseline: sampled from breed distribution, then fixed
            individual_mean = np.random.normal(val, std * individual_offset_scale)
            baseline[signal] = max(0, individual_mean)
    return baseline


def inject_cognitive_drift(baseline, drift_start_month, drift_severity=0.25):
    """
    Simulate gradual individual-level cognitive drift starting at drift_start_month.
    Severity: 0.0 (none) to 1.0 (extreme).
    
    Pattern: sleep decreases or increases abnormally for the individual,
    activity drops, social score declines, nocturnal restlessness rises.
    This is an illustrative drift model — not a clinically validated signature.
    """
    drifted = baseline.copy()
    drifted["sleep_hours"] = baseline["sleep_hours"] * (1 - drift_severity * 0.3)
    drifted["activity_minutes"] = baseline["activity_minutes"] * (1 - drift_severity * 0.4)
    drifted["social_score"] = max(0, baseline["social_score"] - drift_severity * 2.5)
    drifted["nocturnal_restlessness"] = baseline["nocturnal_restlessness"] * (1 + drift_severity * 1.5)
    drifted["vocalization"] = baseline["vocalization"] * (1 + drift_severity * 0.5)
    return drifted


def generate_context_event():
    """
    Returns a context label and its behavioral modifiers.
    Contexts disrupt the behavioral signal — modeling real-world noise.
    """
    events = {
        "normal": {"prob": 0.82, "sleep_mod": 1.0, "activity_mod": 1.0, "social_mod": 1.0},
        "travel": {"prob": 0.05, "sleep_mod": 0.85, "activity_mod": 1.2, "social_mod": 0.7},
        "boarding": {"prob": 0.04, "sleep_mod": 0.80, "activity_mod": 0.9, "social_mod": 0.6},
        "owner_absent": {"prob": 0.05, "sleep_mod": 0.90, "activity_mod": 0.7, "social_mod": 0.5},
        "illness_minor": {"prob": 0.02, "sleep_mod": 1.20, "activity_mod": 0.5, "social_mod": 0.6},
        "new_environment": {"prob": 0.02, "sleep_mod": 0.85, "activity_mod": 1.1, "social_mod": 0.8},
    }
    labels = list(events.keys())
    probs = [events[e]["prob"] for e in labels]
    choice = np.random.choice(labels, p=probs)
    return choice, events[choice]


def is_missing(context, drift_active):
    """
    Data missingness model:
    - Sensor dropout: random
    - Context-driven: higher during travel/boarding (device not worn)
    - The *pattern* of missingness is itself informative (Missing Data Paradox)
    """
    if context in ["travel", "boarding"]:
        return np.random.random() < 0.35  # 35% missing during travel/boarding
    if context == "owner_absent":
        return np.random.random() < 0.15
    return np.random.random() < 0.04  # ~4% random sensor dropout


def generate_dog_record(dog_id, breed, age_group, has_drift=False, drift_month=None, drift_severity=0.25):
    """Generate 12 months of daily records for a single dog."""
    
    profile = BREED_PROFILES[breed]
    baseline = generate_individual_baseline(profile, age_group)
    
    if has_drift and drift_month is None:
        drift_month = np.random.randint(6, 10)  # drift starts in months 6-9
    
    start_date = datetime(2025, 1, 1)
    records = []
    
    for day in range(365):
        current_date = start_date + timedelta(days=day)
        current_month = current_date.month  # 1-12
        
        # Determine if drift is active
        drift_active = has_drift and current_month >= drift_month
        
        # Get current behavioral target (baseline or drifted)
        if drift_active:
            progress = min(1.0, (current_month - drift_month) / 4)  # gradual over 4 months
            drifted = inject_cognitive_drift(baseline, drift_month, drift_severity * progress)
            target = drifted
        else:
            target = baseline
        
        # Context event
        context, ctx_mod = generate_context_event()
        
        # Data missingness
        missing = is_missing(context, drift_active)
        
        if missing:
            records.append({
                "dog_id": dog_id,
                "date": current_date.strftime("%Y-%m-%d"),
                "month": current_month,
                "breed": breed,
                "age_group": age_group,
                "has_drift": has_drift,
                "drift_active": drift_active,
                "context": context,
                "data_missing": True,
                "missingness_type": "systemic" if context in ["travel", "boarding"] else "sensor_dropout",
                "sleep_hours": np.nan,
                "activity_minutes": np.nan,
                "social_score": np.nan,
                "nocturnal_restlessness": np.nan,
                "vocalization_events": np.nan,
            })
        else:
            # Add daily noise + context modifiers
            noise_scale = 0.08  # 8% daily noise

            sleep = max(0, np.random.normal(
                target["sleep_hours"] * ctx_mod["sleep_mod"],
                profile["sleep_hours_std"] * noise_scale
            ))
            activity = max(0, np.random.normal(
                target["activity_minutes"] * ctx_mod["activity_mod"],
                profile["activity_minutes_std"] * noise_scale
            ))
            social = max(0, min(10, np.random.normal(
                target["social_score"] * ctx_mod["social_mod"],
                profile["social_score_std"] * noise_scale
            )))
            restlessness = max(0, np.random.normal(
                target["nocturnal_restlessness"],
                profile["nocturnal_restlessness_std"] * noise_scale
            ))
            vocal = max(0, np.random.normal(
                target["vocalization"] * 1.0,
                profile["vocalization_std"] * noise_scale
            ))
            
            records.append({
                "dog_id": dog_id,
                "date": current_date.strftime("%Y-%m-%d"),
                "month": current_month,
                "breed": breed,
                "age_group": age_group,
                "has_drift": has_drift,
                "drift_active": drift_active,
                "context": context,
                "data_missing": False,
                "missingness_type": None,
                "sleep_hours": round(sleep, 2),
                "activity_minutes": round(activity, 1),
                "social_score": round(social, 2),
                "nocturnal_restlessness": round(restlessness, 2),
                "vocalization_events": round(vocal, 1),
            })
    
    return records


def generate_cohort(n_dogs=100, drift_rate=0.25):
    """
    Generate full synthetic cohort.
    drift_rate: proportion of dogs with simulated behavioral drift.
    """
    all_records = []
    
    print(f"Generating synthetic cohort: {n_dogs} dogs, {drift_rate*100:.0f}% with behavioral drift...")
    
    for i in range(n_dogs):
        dog_id = f"DOG_{i+1:04d}"
        breed = np.random.choice(BREEDS)
        age_group = np.random.choice(AGE_GROUPS, p=[0.3, 0.4, 0.3])
        has_drift = np.random.random() < drift_rate
        drift_severity = np.random.uniform(0.15, 0.40) if has_drift else 0.0
        
        records = generate_dog_record(
            dog_id=dog_id,
            breed=breed,
            age_group=age_group,
            has_drift=has_drift,
            drift_severity=drift_severity
        )
        all_records.extend(records)
        
        if (i + 1) % 20 == 0:
            print(f"  {i+1}/{n_dogs} dogs generated...")
    
    df = pd.DataFrame(all_records)
    print(f"\nDataset shape: {df.shape}")
    print(f"Dogs with drift: {df[df['has_drift']]['dog_id'].nunique()}")
    print(f"Missing data rate: {df['data_missing'].mean()*100:.1f}%")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    return df


if __name__ == "__main__":
    df = generate_cohort(n_dogs=100, drift_rate=0.25)
    
    os.makedirs("data", exist_ok=True)
    output_path = "data/synthetic_doggraph_sample.csv"
    df.to_csv(output_path, index=False)
    print(f"\nDataset saved to: {output_path}")
    print(f"\nBreed distribution:\n{df.groupby('breed')['dog_id'].nunique()}")
    print(f"\nAge group distribution:\n{df.groupby('age_group')['dog_id'].nunique()}")
