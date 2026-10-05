import pandas as pd
import numpy as np
import os

def generate_sample_csv(filename='sample_students_100.csv', n_students=100):
    # Set seed for reproducibility
    np.random.seed(42)

    # Generate features
    student_id = np.arange(1, n_students + 1)
    
    # Study hours (mean 5, std 2, clamped 1-12)
    study_hours = np.clip(np.random.normal(loc=5.0, scale=2.0, size=n_students), 1, 12).round(1)
    
    # Attendance (mean 80, std 12, clamped 40-100)
    attendance = np.clip(np.random.normal(loc=80, scale=12, size=n_students), 40, 100).astype(int)
    
    # Sleep hours (mean 7, std 1.2, clamped 4-10)
    sleep_hours = np.clip(np.random.normal(loc=7.0, scale=1.2, size=n_students), 4, 10).round(1)

    # Generate marks based on study_hours and attendance with noise
    # Base mark + (study_hours * 4.5) + (attendance * 0.45) + random noise
    noise = np.random.normal(loc=0, scale=6, size=n_students)
    marks = 5 + (study_hours * 4.5) + (attendance * 0.45) + noise

    # Clamp marks to realistic 0-100 bounds
    marks = np.clip(marks, 0, 100).round(1)

    # Create DataFrame
    df = pd.DataFrame({
        'student_id': student_id,
        'study_hours': study_hours,
        'attendance': attendance,
        'sleep_hours': sleep_hours,
        'marks': marks
    })

    # Save to file
    df.to_csv(filename, index=False)
    print(f"Successfully generated '{filename}' with {len(df)} realistic rows!")
    print("Marks positively correlate with study_hours and attendance.")

if __name__ == '__main__':
    generate_sample_csv()
