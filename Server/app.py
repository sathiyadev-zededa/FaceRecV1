from flask import Flask, render_template, request
import json
from datetime import datetime

app = Flask(__name__)

def get_sorted_entries():
    entries = []

    with open('log.json', 'r') as file:
        for line in file:
            try:
                entry = json.loads(line)
                entries.append(entry)
            except json.JSONDecodeError:
                pass  # Ignore invalid lines

    sorted_entries = sorted(entries, key=lambda x: datetime.strptime(x['Time'], '%Y-%m-%d %H:%M:%S'))
    return sorted_entries


@app.route('/', methods=['GET', 'POST'])
def index():
    entries = get_sorted_entries()

    if request.method == 'POST':
        search_name = request.form.get('search_name')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')

        filtered_entries = []
        for entry in entries:
            entry_time = datetime.strptime(entry['Time'], '%Y-%m-%d %H:%M:%S')
            if (not search_name or search_name.lower() in entry['Name'].lower()) and \
                    (not start_time or entry_time >= datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')) and \
                    (not end_time or entry_time <= datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')):
                filtered_entries.append(entry)
        entries = filtered_entries

    return render_template('index.html', entries=entries)


if __name__ == '__main__':
    app.run(debug=True)
