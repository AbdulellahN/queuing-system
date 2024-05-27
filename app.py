from flask import Flask, render_template, request, redirect, url_for, session
from dotenv import load_dotenv
from pathlib import Path
from bleach import clean
import bleach
import mysql.connector
import configparser
import json
import os

# Load environment variables
load_dotenv()
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'Q@5mk8wk')

# Load configuration
config = configparser.ConfigParser()
config.read('config.ini')

# Database configurations
db_config = {
    'host': config['Database']['db_host'],
    'user': config['Database']['db_user'],
    'password': config['Database']['db_password'],
    'database': config['Database']['db_database'],
    'port': int(config['Database']['db_port']),
}
crl_db_config = {
    'host': config['Database']['crl_db_host'],
    'user': config['Database']['crl_db_user'],
    'password': config['Database']['crl_db_password'],
    'database': config['Database']['crl_db_database'],
    'port': int(config['Database']['crl_db_port']),
}

# Load template data from config.json
with open('config.json', 'r') as file:
    template_data = json.load(file)

# Initialize database connections
db_connection = None
db_cursor = None
crl_db_connection = None
crl_db_cursor = None

def connect_to_database():
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(buffered=True)
        print("Database connection established successfully.")
        return connection, cursor
    except mysql.connector.Error as e:
        print(f"Error connecting to database: {e}")
        return None, None

def connect_to_database_crl():
    try:
        connection = mysql.connector.connect(**crl_db_config)
        cursor = connection.cursor(buffered=True)
        print("CRL database connection established successfully.")
        return connection, cursor
    except mysql.connector.Error as e:
        print(f"Error connecting to CRL database: {e}")
        return None, None

# Establish initial database connections
db_connection, db_cursor = connect_to_database()
crl_db_connection, crl_db_cursor = connect_to_database_crl()

@app.before_request
def before_request():
    if 'template_paths' not in session:
        session['template_paths'] = template_data['template_paths']
    if 'template_content' not in template_data:
        template_data['template_content'] = {}  # Initialize template_content as an empty dictionary
    if 'template_content' not in session:
        session['template_content'] = template_data['template_content']

def edit_email_template(template_id, language, subject, content, footer):
    # Load the existing template data from the JSON file
    config_path = Path('config.json')
    with open(config_path, 'r') as f:
        config_data = json.load(f)

    # Find the template to be edited
    template_paths = config_data.get('template_paths', {})
    language_templates = template_paths.get(language, {})
    template_data = language_templates.get(template_id, None)

    if template_data is None:
        return {'success': False, 'message': 'Template not found'}

    # Update the template data
    template_data['placeholders']['title'] = subject
    template_data['placeholders']['paragraph'] = content
    template_data['placeholders']['footer'] = footer

    # Save the updated template data to the JSON file
    with open(config_path, 'w') as f:
        json.dump(config_data, f, indent=2)

    # Update the corresponding HTML file
    file_path = Path(template_data['file_path'])
    with open(file_path, 'r') as f:
        html_content = f.read()

    placeholders = template_data['placeholders']
    updated_html = html_content.replace('{{title}}', placeholders['title'])
    updated_html = updated_html.replace('{{paragraph}}', placeholders['paragraph'])
    updated_html = updated_html.replace('{{footer}}', placeholders['footer'])

    with open(file_path, 'w') as f:
        f.write(updated_html)

    return {'success': True, 'message': 'Template updated successfully'}

# Define route handlers
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/emails')
def emails():
    if crl_db_cursor:
        try:
            query = "SELECT * FROM crl.renewed"
            crl_db_cursor.execute(query)
            emails = crl_db_cursor.fetchall()
            return render_template('emails.html', emails=emails)
        except Exception as e:
            return f"Error fetching emails: {e}"
    else:
        return "Database connection is not established."

@app.route('/edit_form', methods=['GET'])
def edit_form():
    return render_template('edit_form.html')

@app.route('/edit_template', methods=['GET', 'POST'])
def edit_template():
    if request.method == 'POST':
        language = request.form.get('language')
        template_id = request.form.get('template_id')

        if language and template_id:
            # Load template path and placeholders from config.json
            with open('config.json', 'r') as file:
                config_data = json.load(file)

            if language in config_data['template_paths'] and template_id in config_data['template_paths'][language]:
                template_data = config_data['template_paths'][language][template_id]
                file_path = template_data['file_path']
                placeholders = template_data['placeholders']

                return render_template('edit_template.html', language=language, template_id=template_id, placeholders=placeholders)

    return render_template('edit_form.html')

@app.route('/edit_email_template', methods=['POST'])
def edit_email_template_route():
    template_id = request.form.get('template_id')
    language = request.form.get('language')
    subject = request.form.get('subject')
    content = request.form.get('content')
    footer = request.form.get('footer')

    if template_id and language and subject and content and footer:
        result = edit_email_template(template_id, language, subject, content, footer)
        if result['success']:
            # Initialize the language key if it doesn't exist
            if language not in session['template_content']:
                session['template_content'][language] = {}

            # Store the updated template content
            session['template_content'][language][template_id] = {
                'subject': subject,
                'content': content,
                'footer': footer
            }
            return 'Template updated successfully', 200
        else:
            return result['message'], 404
    else:
        return 'Missing required parameters', 400

@app.route('/update_template', methods=['GET'])
def update_template():
    language = request.args.get('language')
    template_id = request.args.get('template_id')

    if language and template_id:
        # Load the template data from config.json
        config_path = Path('config.json')
        with open(config_path, 'r') as f:
            config_data = json.load(f)

        # Find the template to be updated
        template_paths = config_data.get('template_paths', {})
        language_templates = template_paths.get(language, {})
        template_data = language_templates.get(template_id, None)

        if template_data is not None:
            # Update the corresponding HTML file with the new content from the session
            file_path = Path(template_data['file_path'])
            template_content = session['template_content'][language][template_id]

            with open(file_path, 'r') as f:
                html_content = f.read()

            updated_html = html_content.replace('{{title}}', template_content['subject'])
            updated_html = updated_html.replace('{{paragraph}}', template_content['content'])
            updated_html = updated_html.replace('{{footer}}', template_content['footer'])

            with open(file_path, 'w') as f:
                f.write(updated_html)

            return 'Template updated successfully', 200

    return 'Template not found', 404

if __name__ == '__main__':
    db_connection, db_cursor = connect_to_database()
    crl_db_connection, crl_db_cursor = connect_to_database_crl()
    app.run(debug=True)
