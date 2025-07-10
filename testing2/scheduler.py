from datetime import datetime, timedelta

# Constants
STUDY_HOURS = {
    "morning": (9, 12),
    "afternoon": (12, 17),
    "evening": (17, 19),
    "night": (20, 24)
}
SLEEP_HOURS = range(0, 8)
DEFAULT_ATTENTION_SPAN = 60

# Generate 30 days worth of time blocks, each 30 minutes
def generate_time_blocks(start_date, days=30):
    blocks = []
    for i in range(days):
        day = datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=i)
        for hour in range(8, 24):
            start = datetime(day.year, day.month, day.day, hour)
            end = start + timedelta(minutes=30)
            blocks.append((start, end))
    return blocks

# Expand fixed commitments to repeat weekly for 30 days
def expand_fixed_commitments(fixed_commitments, days=30):
    repeated = []
    for item in fixed_commitments:
        subject = item["subject"]
        original_start = datetime.strptime(item["start"], "%Y-%m-%dT%H:%M")
        original_end = datetime.strptime(item["end"], "%Y-%m-%dT%H:%M")
        weekday = original_start.weekday()

        for i in range(days):
            current_day = datetime.now().date() + timedelta(days=i)
            if current_day.weekday() == weekday:
                new_start = datetime.combine(current_day, original_start.time())
                new_end = datetime.combine(current_day, original_end.time())
                repeated.append((subject, new_start, new_end))
    return repeated

# Filter time blocks based on user preferences and fixed commitments
def filter_study_blocks(time_blocks, user_prefs, fixed):
    preferred_hours = []
    for pref in user_prefs["preferredTimes"]:
        start_h, end_h = STUDY_HOURS.get(pref, (0, 0))
        preferred_hours += list(range(start_h, end_h))

    filtered = []
    for start, end in time_blocks:
        if start.hour not in preferred_hours or start.hour in SLEEP_HOURS:
            continue
        if any(fs <= start < fe or fs < end <= fe for (_, fs, fe) in fixed):
            continue
        filtered.append((start, end))
    return filtered

# Break long tasks into chunks based on attention span
def split_task(task_time, attention_span):
    parts = []
    while task_time > 0:
        part = min(attention_span, task_time)
        parts.append(part)
        task_time -= part
    return parts

# Main function to generate schedule
def generate_schedule(fixed_commitments, tasks, user_preferences):
    # Expand repeating fixed commitments
    fixed = expand_fixed_commitments(fixed_commitments)

    # Sort tasks by priority and due date urgency
    def task_sort_key(t):
        days_left = (datetime.strptime(t["due"], "%Y-%m-%d") - datetime.now()).days
        urgency_bonus = 0 if days_left > 7 else (7 - days_left)
        return (t["priority"] - urgency_bonus)

    sorted_tasks = sorted(tasks, key=task_sort_key)
    attention = user_preferences.get("attentionSpan", DEFAULT_ATTENTION_SPAN)

    # Generate available blocks over 30 days
    blocks = generate_time_blocks(datetime.now().strftime("%Y-%m-%d"), days=30)
    available_blocks = filter_study_blocks(blocks, user_preferences, fixed)

    schedule = []

    # Add fixed commitments first
    for subject, start, end in fixed:
        schedule.append({
            "type": "Fixed Commitment",
            "subject": subject,
            "start": start.strftime("%Y-%m-%d %H:%M"),
            "end": end.strftime("%Y-%m-%d %H:%M")
        })

    # Schedule tasks into free slots
    block_index = 0
    for task in sorted_tasks:
        parts = split_task(task["estimated"], attention)

        for duration in parts:
            if block_index >= len(available_blocks):
                break
            start = available_blocks[block_index][0]
            end = start + timedelta(minutes=duration)

            schedule.append({
                "type": "Task",
                "subject": task["subject"],
                "start": start.strftime("%Y-%m-%d %H:%M"),
                "end": end.strftime("%Y-%m-%d %H:%M")
            })

            block_index += 1

            if user_preferences.get("preferBreaks") and block_index < len(available_blocks):
                block_index += 1  # Skip 1 block for break

    # Sort final schedule by start time
    schedule.sort(key=lambda x: x["start"])
    return schedule
