from flask import Flask, render_template, request
import mysql.connector
import configparser

app = Flask(__name__)

# Load configuration
config = configparser.ConfigParser()
config.read('config.ini')

# Database connection setup
db_config = {
    'host': config['Database']['crl_db_host'],
    'user': config['Database']['crl_db_user'],
    'password': config['Database']['crl_db_password'],
    'database': config['Database']['crl_db_database'],
    'port': int(config['Database']['crl_db_port']),
}
db_connection = None
db_cursor = None

try:
    db_connection = mysql.connector.connect(**db_config)
    db_cursor = db_connection.cursor(buffered=True)
    print("Database connection established successfully.")
except mysql.connector.Error as e:
    print(f"Error connecting to database: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/emails')
def emails():
    try:
        if db_cursor:
            # Fetch emails from database
            query = "SELECT * FROM crl.renewed"
            db_cursor.execute(query)
            emails = db_cursor.fetchall()
            return render_template('emails.html', emails=emails)
        else:
            return "Database connection is not established."
    except Exception as e:
        return f"Error fetching emails: {e}"

@app.route('/edit_template', methods=['GET', 'POST'])
def edit_template():
    if request.method == 'POST':
        try:
            new_template = request.form['new_template']
            # Save new_template to config or file (for demonstration, print the new template)
            print(f"New template content: {new_template}")
            return "Template updated successfully"
        except Exception as e:
            return f"Error updating template: {e}"
    else:
        # Display form to edit template
        current_template = config['Templates']['email_temp_path']
        return render_template('edit_template.html', current_template=current_template)

@app.route('/change_schedule', methods=['POST'])
def change_schedule():
    if request.method == 'POST':
        try:
            new_schedule = request.form['new_schedule']
            # Update schedule logic here (for demonstration, print the new schedule)
            print(f"New schedule: {new_schedule}")
            return "Schedule updated successfully"
        except Exception as e:
            return f"Error changing schedule: {e}"
    else:
        return "Invalid request method for changing schedule."

if __name__ == '__main__':
    app.run(debug=True)
