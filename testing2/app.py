from flask import Flask, request, jsonify, render_template
from scheduler import generate_schedule

app = Flask(__name__, static_folder='static', template_folder='templates')

# Homepage route
@app.route('/')
def homepage():
    return render_template('homepage.html')

# Each HTML page route
@app.route('/fixed_commitments.html')
def fixed_commitments():
    return render_template('fixed_commitments.html')

@app.route('/task_details.html')
def task_details():
    return render_template('task_details.html')

@app.route('/preferences.html')
def user_preferences():
    return render_template('preferences.html')

@app.route('/output.html')
def output():
    return render_template('output.html')

# Schedule generation endpoint
@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json()
    fixed_commitments = data.get("commitments", [])
    tasks = data.get("tasks", [])
    preferences = data.get("preferences", {})

    schedule = generate_schedule(fixed_commitments, tasks, preferences)
    return jsonify({ "schedule": schedule })

if __name__ == "__main__":
    app.run(debug=True)
