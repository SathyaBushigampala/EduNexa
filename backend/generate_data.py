import pandas as pd
import numpy as np

def generate_dataset(filename="dataset.csv"):
    np.random.seed(42)  # For reproducibility
    n = 200
    
    student_id = np.arange(1, n + 1)
    
    # study_hours_per_day (2 to 9, continuous)
    study_hours_per_day = np.random.uniform(2, 9, n)
    
    # attendance_percentage (50 to 100)
    attendance_percentage = np.random.uniform(50, 100, n)
    
    # sleep_hours (4 to 9)
    sleep_hours = np.random.uniform(4, 9, n)
    
    days_absent_base = 20 * (100 - attendance_percentage) / 100
    days_absent_per_month = np.random.poisson(days_absent_base)
    days_absent_per_month = np.clip(days_absent_per_month, 0, 10).astype(int)
    
    # Corrected logical relationship for marks
    # Zero study + zero attendance + zero sleep = ~0 marks (intercept)
    # study_hours impact: ~4.0 marks per hour
    # attendance impact: ~0.4 marks per %
    # sleep_hours impact: ~3.0 marks per hour
    # Random noise: std=4 to prevent overpowering the signal
    
    noise = np.random.normal(0, 4, n)
    
    marks = (
        0.0 + # Intercept
        (study_hours_per_day * 4.0) +
        (attendance_percentage * 0.4) +
        (sleep_hours * 3.0) +
        noise
    )
    
    # Clip between 0 and 100 and round to 1 decimal place
    marks = np.clip(marks, 0, 100).round(1)
    
    # pass_fail (derived: marks >= 40)
    pass_fail = (marks >= 40).astype(int)
    
    df = pd.DataFrame({
        "student_id": student_id,
        "study_hours_per_day": study_hours_per_day.round(2),
        "attendance_percentage": attendance_percentage.round(2),
        "sleep_hours": sleep_hours.round(2),
        "days_absent_per_month": days_absent_per_month,
        "marks": marks,
        "pass_fail": pass_fail
    })
    
    df.to_csv(filename, index=False)
    print(f"Dataset with {n} records saved to {filename}")
    return df

if __name__ == "__main__":
    generate_dataset()
