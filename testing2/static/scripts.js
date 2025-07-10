// ========== Shared Storage Functions ==========
function getData(key) {
  return JSON.parse(localStorage.getItem(key)) || [];
}

function saveData(key, data) {
  localStorage.setItem(key, JSON.stringify(data));
}

// ========== Page Navigation ==========
function goToNext() {
  const current = window.location.pathname;
  if (current.includes("fixed_commitments")) {
    window.location.href = "task_details.html";
  } else if (current.includes("task_details")) {
    window.location.href = "preferences.html";
  }
}

// ========== Fixed Commitments ==========
function addCommitment() {
  const subject = document.getElementById('subject').value;
  const start = document.getElementById('startTime').value;
  const end = document.getElementById('endTime').value;

  if (!subject || !start || !end) {
    alert("Please fill in all fields.");
    return;
  }

  const commitments = getData("fixedCommitments");
  commitments.push({ subject, start, end });
  saveData("fixedCommitments", commitments);

  const table = document.getElementById("commitmentsTable");
  const row = table.insertRow();
  row.insertCell(0).innerText = subject;
  row.insertCell(1).innerText = start;
  row.insertCell(2).innerText = end;

  document.getElementById('subject').value = '';
  document.getElementById('startTime').value = '';
  document.getElementById('endTime').value = '';
}

// ========== Task Details ==========
function addTask() {
  const subject = document.getElementById('taskSubject').value;
  const estimated = document.getElementById('estimatedTime').value;
  const due = document.getElementById('dueDate').value;
  const priority = document.getElementById('priority').value;

  if (!subject || !estimated || !due || !priority) {
    alert("Please fill in all fields.");
    return;
  }

  const tasks = getData("taskDetails");
  tasks.push({
    subject,
    estimated: parseInt(estimated),
    due,
    priority: parseInt(priority)
  });
  saveData("taskDetails", tasks);

  const table = document.getElementById("tasksTable");
  const row = table.insertRow();
  row.insertCell(0).innerText = subject;
  row.insertCell(1).innerText = estimated;
  row.insertCell(2).innerText = due;
  row.insertCell(3).innerText = priority;

  document.getElementById('taskSubject').value = '';
  document.getElementById('estimatedTime').value = '';
  document.getElementById('dueDate').value = '';
  document.getElementById('priority').value = '';
}

// ========== Preferences ==========
function generateSchedule() {
  const preferredTimes = Array.from(document.getElementById('preferredTimes').selectedOptions).map(opt => opt.value);
  const preferBreaks = document.getElementById('preferBreaks').checked;
  const workDuration = parseInt(document.getElementById('workDuration').value) || 60;

  const preferences = {
    preferredTimes,
    preferBreaks,
    attentionSpan: workDuration
  };
  saveData("userPreferences", preferences);

  window.location.href = "output.html";
}

// ========== Output Page Logic ==========
document.addEventListener("DOMContentLoaded", function () {
  if (!window.location.pathname.includes("output.html")) return;

  const commitments = getData("fixedCommitments");
  const tasks = getData("taskDetails");
  const prefs = getData("userPreferences");

  fetch("http://localhost:5000/generate", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      commitments,
      tasks,
      preferences: prefs
    })
  })
    .then(res => res.json())
    .then(data => {
      const calendar = document.getElementById("calendar");
      const schedule = data.schedule;

      // Group schedule by day
      const grouped = {};
      schedule.forEach(item => {
        const date = item.start.split(" ")[0];
        if (!grouped[date]) grouped[date] = [];
        grouped[date].push(item);
      });

      // Create 30-day calendar grid
      const today = new Date();
      for (let i = 0; i < 30; i++) {
        const dateObj = new Date(today);
        dateObj.setDate(today.getDate() + i);
        const dateStr = dateObj.toISOString().split("T")[0];

        const dayDiv = document.createElement("div");
        dayDiv.className = "day";
        dayDiv.innerHTML = `<strong>${dateStr}</strong><br>`;

        if (grouped[dateStr]) {
          grouped[dateStr].forEach(item => {
            const entry = document.createElement("div");
            entry.className = "entry " + (item.type === "Fixed Commitment" ? "fixed" : "task");
            entry.innerHTML = `<strong>${item.subject}</strong><br>${item.start.split(" ")[1]} - ${item.end.split(" ")[1]}`;
            dayDiv.appendChild(entry);
          });
        } else {
          dayDiv.innerHTML += `<em>No items</em>`;
        }

        calendar.appendChild(dayDiv);
      }

      // Store schedule for CSV export
      localStorage.setItem("finalSchedule", JSON.stringify(schedule));
    })
    .catch(err => {
      console.error(err);
      alert("Error loading schedule. Make sure the backend is running.");
    });
});

// ========== Download CSV ==========
function downloadCSV() {
  const schedule = getData("finalSchedule");
  if (schedule.length === 0) {
    alert("No schedule available to download.");
    return;
  }

  let csvContent = "Type,Subject,Start,End\n";
  schedule.forEach(item => {
    csvContent += `${item.type},${item.subject},${item.start},${item.end}\n`;
  });

  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");

  link.setAttribute("href", url);
  link.setAttribute("download", "study_schedule.csv");
  link.style.display = "none";

  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}
