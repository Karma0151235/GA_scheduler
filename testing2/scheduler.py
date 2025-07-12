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

DAY_NAME_TO_INDEX = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
    "Saturday": 5,
    "Sunday": 6
}

def generate_time_blocks(start_date, days=30):
    blocks = []
    for i in range(days):
        day = datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=i)
        for hour in range(8, 24):
            start = datetime(day.year, day.month, day.day, hour)
            end = start + timedelta(minutes=30)
            blocks.append((start, end))
    return blocks

# 🆕 Fixed commitments now use day name + start/end time
def expand_fixed_commitments(fixed_commitments, days=30):
    repeated = []
    for item in fixed_commitments:
        subject = item["subject"]
        weekday_name = item["day"]
        weekday = DAY_NAME_TO_INDEX.get(weekday_name, -1)

        if weekday == -1:
            continue  # Invalid weekday, skip it

        start_time_obj = datetime.strptime(item["startTime"], "%H:%M").time()
        end_time_obj = datetime.strptime(item["endTime"], "%H:%M").time()

        for i in range(days):
            current_day = datetime.now().date() + timedelta(days=i)
            if current_day.weekday() == weekday:
                new_start = datetime.combine(current_day, start_time_obj)
                new_end = datetime.combine(current_day, end_time_obj)
                repeated.append((subject, new_start, new_end))
    return repeated

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

def split_task(task_time, attention_span):
    parts = []
    while task_time > 0:
        part = min(attention_span, task_time)
        parts.append(part)
        task_time -= part
    return parts

def generate_schedule(fixed_commitments, tasks, user_preferences):
    fixed = expand_fixed_commitments(fixed_commitments)

    def task_sort_key(t):
        days_left = (datetime.strptime(t["due"], "%Y-%m-%d") - datetime.now()).days
        urgency_bonus = 0 if days_left > 7 else (7 - days_left)
        return (t["priority"] - urgency_bonus)

    sorted_tasks = sorted(tasks, key=task_sort_key)
    attention = user_preferences.get("attentionSpan", DEFAULT_ATTENTION_SPAN)

    blocks = generate_time_blocks(datetime.now().strftime("%Y-%m-%d"), days=30)
    available_blocks = filter_study_blocks(blocks, user_preferences, fixed)

    schedule = []

    for subject, start, end in fixed:
        schedule.append({
            "type": "Fixed Commitment",
            "subject": subject,
            "start": start.strftime("%Y-%m-%d %H:%M"),
            "end": end.strftime("%Y-%m-%d %H:%M")
        })

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
                block_index += 1

    schedule.sort(key=lambda x: x["start"])
    return schedule
