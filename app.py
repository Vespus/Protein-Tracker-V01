from flask import Flask, render_template, request, redirect, url_for, make_response

import json, csv, io, os, shutil, glob
from datetime import datetime, date, timedelta

app = Flask(__name__)

@app.template_filter('abs')
def abs_filter(value):
    return abs(value)

def load_data(filename):
    try:
        with open(filename, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return []

def save_data(data, filename):
    with open(filename, "w") as file:
        json.dump(data, file)


###########
# ROOT
###########

@app.route('/', methods=['GET', 'POST'])
def index():
    protein_data = load_data("protein_data.txt")
    protein_data.sort(key=lambda x: x['date'], reverse=True)
    protein_types = load_data("protein_types.txt")

    if request.method == 'POST':
        protein_type = request.form.get('protein_type')
        if protein_type == "Other":
            protein_type = request.form.get('other_protein_type')
            protein_types.append(protein_type)
            save_data(protein_types, "protein_types.txt")
        grams = int(request.form.get('grams'))
        protein_data.append({"date": datetime.today().strftime('%Y-%m-%d'), "protein_type": protein_type, "grams": grams})
        save_data(protein_data, "protein_data.txt")
        return redirect(url_for('index'))

    current_date = date.today().strftime('%Y-%m-%d')
    protein_data_today = [data for data in protein_data if data["date"] == current_date]

    total_grams_today = sum(entry["grams"] for entry in protein_data_today)

    total_grams_per_day = {}
    for entry in protein_data:
        if entry["date"] not in total_grams_per_day:
            total_grams_per_day[entry["date"]] = 0
        total_grams_per_day[entry["date"]] += entry["grams"]

    total_grams_per_day = {k: v for k, v in sorted(total_grams_per_day.items(), key=lambda item: item[0], reverse=True)}

    goal = load_data("goal.txt")
    if not goal:  
        goal = 0  
    else:  
        goal = goal[0]  
    return render_template('index.html', protein_data=protein_data_today, protein_types=protein_types, total_grams_per_day=total_grams_per_day, current_date=current_date, datetime=datetime, goal=goal, total_grams_today=total_grams_today)


###########
# CHARTS
###########

@app.route('/chart', methods=['GET', 'POST'])
def chart():
    protein_data = load_data("protein_data.txt")

    # Set the default start date to 7 days ago and exclude today
    eight_days_ago = (datetime.now() - timedelta(days=8)).strftime('%Y-%m-%d')
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    start_date = eight_days_ago
    end_date = yesterday

    if request.method == 'POST':
        start_date = request.form.get('start_date') or start_date
        end_date = request.form.get('end_date')

    # Filter the protein_data based on start and end dates
    if start_date:
        protein_data = [d for d in protein_data if d['date'] >= start_date]
    if end_date:
        protein_data = [d for d in protein_data if d['date'] <= end_date]

    total_grams_per_day = {}
    total_grams_by_type_per_day = {}
    protein_types = load_data("protein_types.txt")

    for entry in protein_data:
        if entry["date"] not in total_grams_per_day:
            total_grams_per_day[entry["date"]] = 0
            total_grams_by_type_per_day[entry["date"]] = {ptype: 0 for ptype in protein_types}

        # Add new protein types to protein_types list and total_grams_by_type_per_day dictionary
        if entry["protein_type"] not in protein_types:
            protein_types.append(entry["protein_type"])
            for date in total_grams_by_type_per_day:
                total_grams_by_type_per_day[date][entry["protein_type"]] = 0

        total_grams_per_day[entry["date"]] += entry["grams"]
        total_grams_by_type_per_day[entry["date"]][entry["protein_type"]] += entry["grams"]

    total_grams_per_day = {k: v for k, v in sorted(total_grams_per_day.items(), key=lambda item: item[0])}
    total_grams_by_type_per_day = {k: v for k, v in sorted(total_grams_by_type_per_day.items(), key=lambda item: item[0])}

    dates = list(total_grams_per_day.keys())
    total_grams = list(total_grams_per_day.values())
    total_grams_by_type = [total_grams_by_type_per_day[date] for date in dates]

    goal = load_data("goal.txt")
    if not goal:  
        goal = 0  
    else:  
        goal = goal[0]  

    # Compute pie_labels and pie_data
    total_grams_by_type_overall = {ptype: 0 for ptype in protein_types}
    for grams_by_type in total_grams_by_type_per_day.values():
        for ptype, grams in grams_by_type.items():
            total_grams_by_type_overall[ptype] += grams

    pie_labels = list(total_grams_by_type_overall.keys())
    pie_data = list(total_grams_by_type_overall.values())

    # Compute average consumption
    if dates:
        total_days = len(dates)
        total_consumption = sum(total_grams)
        average_consumption = round(total_consumption / total_days)
    else:
        average_consumption = 0


    # Calculate consumption_diff
    consumption_diff = average_consumption - goal

    # Format start and end dates to German date format (dd.mm.yy)
    start_date_formatted = datetime.strptime(start_date, '%Y-%m-%d').strftime('%d.%m.%y')
    end_date_formatted = datetime.strptime(end_date, '%Y-%m-%d').strftime('%d.%m.%y')
    date_range = "Vom {} bis {}:".format(start_date_formatted, end_date_formatted)

    return render_template('chart.html', dates=dates, total_grams=total_grams, total_grams_by_type=total_grams_by_type, goal=goal, pie_labels=pie_labels, pie_data=pie_data, average_consumption=average_consumption, date_range=date_range, consumption_diff=consumption_diff)


  

###########
# SETTINGS
###########

@app.route('/settings', methods=['GET', 'POST'])
def settings():

    
    if request.method == 'POST':
        weight = request.form.get('weight')
        multiplier = request.form.get('multiplier')
        goal = [int(weight) * int(multiplier)] 
        save_data(goal, "goal.txt")
        return redirect(url_for('settings'))

    goal = load_data("goal.txt")
    if not goal: 
        goal = 0  
    else:  
        goal = goal[0]  

    # Get a list of backup files
    backup_files = glob.glob("backup/protein_data_*.txt")
  
    return render_template('settings.html', goal=goal, backup_files=backup_files)


###########
# EXPORT
###########

@app.route('/export', methods=['GET', 'POST'])
def export():
    if request.method == 'POST':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        delimiter = request.form.get('delimiter', '\t')
        filename = request.form.get('filename', f"Proteinexport-{start_date}-{end_date}.csv")
        
        # map delimiter
        delimiter_map = {'\\t': '\t', '\\n': '\n', '\\r': '\r'}
        delimiter = delimiter_map.get(delimiter, delimiter)
        
        protein_data = load_data("protein_data.txt")
        filtered_data = [entry for entry in protein_data if (not start_date or entry['date'] >= start_date) and (not end_date or entry['date'] <= end_date)]
        
        output = io.StringIO()
        writer = csv.writer(output, delimiter=delimiter)
        writer.writerow(['date', 'protein_type', 'grams'])
        for entry in filtered_data:
            writer.writerow([entry['date'], entry['protein_type'], entry['grams']])
        
        response = make_response(output.getvalue())
        response.headers["Content-Disposition"] = f"attachment; filename={filename}"
        response.headers["Content-type"] = "text/csv"
        
        return response
    else:
        return render_template('export.html')


###########
# VIEW PROTEIN / HISTORIE
###########

@app.route('/view_protein', methods=['GET', 'POST'])
def view_protein():
    protein_data = load_data("protein_data.txt")
    goal = load_data("goal.txt")
    if not goal:  
        goal = 0  
    else:  
        goal = goal[0]  

    date = None

    if request.method == 'POST':
        if request.form.get('edit') == 'true':
            old_date = request.form.get('old_date')
            old_protein_type = request.form.get('old_protein_type')
            new_date = request.form.get('new_date')
            new_protein_type = request.form.get('new_protein_type')
            new_grams = int(request.form.get('new_grams'))
            
            # Update the protein_data list
            for entry in protein_data:
                if entry['date'] == old_date and entry['protein_type'] == old_protein_type:
                    entry['date'] = new_date
                    entry['protein_type'] = new_protein_type
                    entry['grams'] = new_grams

            save_data(protein_data, "protein_data.txt")
            date = new_date
        else:
            date = request.form.get('date')
    elif request.method == 'GET':
        date = request.args.get('date')

    if date:
        filtered_data = [entry for entry in protein_data if entry["date"] == date]
        total_grams = sum(entry["grams"] for entry in filtered_data)

        protein_type_grams = {}
        for entry in filtered_data:
            if entry['protein_type'] not in protein_type_grams:
                protein_type_grams[entry['protein_type']] = 0
            protein_type_grams[entry['protein_type']] += entry['grams']

        return render_template('view_protein.html', protein_data=filtered_data, total_grams=total_grams, date=date, datetime=datetime, goal=goal, protein_type_grams=protein_type_grams)

    return render_template('view_protein.html', protein_data=None, total_grams=None, datetime=datetime, goal=goal)


###########
# BACKUP
###########

@app.route('/backup', methods=['POST'])
def backup():
    # Create backup folder if it doesn't exist
    if not os.path.exists('backup'):
        os.mkdir('backup')

    src = "protein_data.txt"
    dst = "backup/protein_data_" + datetime.now().strftime('%Y%m%d%H%M%S') + ".txt"
    shutil.copy2(src, dst)  # Copies src file to dst file (or directory)
    return 'Backup created.'


###########
# RESTORE
###########

@app.route('/restore', methods=['POST'])
def restore():
    try:
        # Get a list of backup files
        backup_files = glob.glob("backup/protein_data_*.txt")

        if not backup_files:
            return "No backup files found."

        # Sort the backup files by date
        backup_files.sort(key=os.path.getmtime)

        # Get the most recent backup file
        recent_backup = backup_files[-1]

        # Copy the recent backup file to protein_data.txt
        shutil.copy(recent_backup, "protein_data.txt")

        return "Successfully restored from backup: " + recent_backup
    except Exception as e:
        return "Error occurred while restoring backup: " + str(e)



if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)
    app.logger.info('Starting Flask app')
    app.run(host='0.0.0.0', port=5000, debug=True)