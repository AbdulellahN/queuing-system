import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pika
from jinja2 import Environment, FileSystemLoader
import configparser
import schedule
import time
import datetime
import mysql.connector

def read_config(config_file):
    config = configparser.ConfigParser()
    config.read(config_file)
    return config

config = read_config('config.ini')

crl_db_host = config['Database']['crl_db_host']
crl_db_user = config['Database']['crl_db_user']
crl_db_password = config['Database']['crl_db_password']
crl_db_database = config['Database']['crl_db_database']
crl_db_port = int(config['Database']['crl_db_port'])

try:
    db_connection = mysql.connector.connect(
        host=crl_db_host,
        user=crl_db_user,
        password=crl_db_password,
        database=crl_db_database,
        port=crl_db_port
    )

    if db_connection.is_connected():
        print("Connected to the new database")
except:
    print("error")


db_cursor = db_connection.cursor()
def send_email(email, body):
    smtp_server = config['Email']['smtp_server']
    smtp_port = int(config['Email']['smtp_port'])
    sender_email = config['Email']['sender_email']
    sender_password = config['Email']['sender_password']

    message = MIMEMultipart()
    message['From'] = config['Email']['sender_email']
    message['To'] = email
    message['Subject'] = config['Email']['subject']
    message.attach(MIMEText(body, 'html'))

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, email, message.as_string())
    # Save client to database

def save_client_to_database(license_number, license_type, email, expires_at, status):
    insert_query = "INSERT INTO crl.renewed (license_number, license_type, email, expires_at, status, sent_at) VALUES (%s, %s, %s, %s, %s, %s)"
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data = (license_number, license_type, email, expires_at, status, current_time)
    db_cursor.execute(insert_query, data)
    db_connection.commit()


def check_record_exists(license_number, license_type, email, expires_at):
    config = read_config('config.ini')
    crl_db_host = config['Database']['crl_db_host']
    crl_db_user = config['Database']['crl_db_user']
    crl_db_password = config['Database']['crl_db_password']
    crl_db_database = config['Database']['crl_db_database']
    crl_db_port = int(config['Database']['crl_db_port'])

    try:
        db_connection = mysql.connector.connect(
            host=crl_db_host,
            user=crl_db_user,
            password=crl_db_password,
            database=crl_db_database,
            port=crl_db_port
        )

        db_cursor = db_connection.cursor()

        # Prepare SQL query to check if record exists
        query = "SELECT status FROM crl.renewed WHERE license_number = %s AND license_type = %s AND email = %s AND expires_at = %s"


        db_cursor.execute(query, (license_number, license_type, email, expires_at))


        result = db_cursor.fetchone()

        # If result is not None, record exists, return status
        if result:
            return result[0]  # Status is the first column in the result

        # If result is None, record does not exist
        else:
            return -1

    except mysql.connector.Error as error:
        print("Error:", error)
        return None

def update_status(license_number,new_status):
    config = read_config('config.ini')
    crl_db_host = config['Database']['crl_db_host']
    crl_db_user = config['Database']['crl_db_user']
    crl_db_password = config['Database']['crl_db_password']
    crl_db_database = config['Database']['crl_db_database']
    crl_db_port = int(config['Database']['crl_db_port'])

    try:
        db_connection = mysql.connector.connect(
            host=crl_db_host,
            user=crl_db_user,
            password=crl_db_password,
            database=crl_db_database,
            port=crl_db_port,
        )

        db_cursor = db_connection.cursor()

        update_query = f"UPDATE crl.renewed SET status = {new_status} WHERE license_number = %s"
        db_cursor.execute(update_query, (license_number,))
        db_connection.commit()

    except mysql.connector.Error as err:
        print(f"Error: {err}")

def get_template_name(status):
    # Logic to determine which template to use based on status value
    if status == 0:
        return config["Templates"]["email_template_path"]
    elif status == 1:
        return "template2.html"
    elif status == 2:
        return "template3.html"
    else:
        return "default_template.html"  # Or handle other cases as per your requirement
def process_license_expiry_message(ch, method, properties, type, body):

    data_string = body.decode('utf-8')
    result_list = eval(data_string)


    result_list = [
        item if not isinstance(item, datetime.datetime) else datetime.datetime.strftime(item, "%Y-%m-%d %H:%M:%S") for
        item in result_list]

    email, license_number, license_type, expires_at_str, language = result_list

    expires_at = datetime.datetime.strptime(expires_at_str, "%Y-%m-%d %H:%M:%S")
    status = check_record_exists(license_number, license_type, email, expires_at)

    env = Environment(loader=FileSystemLoader("templates"))

    if language == "ar":
        if status == 0:
            template = env.get_template("s_temp_AR.html")
        elif status == 1:
            template = env.get_template("t_temp_AR.html")
        else:
            template = env.get_template("email_temp_AR.html")
    else:
        if status == 0:
            template = env.get_template("s_temp.html")
        elif status == 1:
            template = env.get_template("t_temp.html")
        else:
            template = env.get_template("email_temp.html")

    email_body = template.render(license_number=license_number, expires_at=expires_at)

    if status == -1:
        new_status = 0
        save_client_to_database(license_number, license_type, email, expires_at, new_status)
    else:
        new_status = status + 1
        update_status(license_number, new_status)

    send_email(email.strip(), email_body)

    print(f"Email sent for license {license_number} to {email}")


def consume_messages():
    rabbitmq_host = config['RabbitMQ']['host']
    rabbitmq_port = int(config['RabbitMQ']['port'])
    rabbitmq_queue_name = config['RabbitMQ']['queue_name']

    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host, port=rabbitmq_port))
    channel = connection.channel()

    channel.queue_declare(queue=rabbitmq_queue_name, durable=True)
    channel.basic_consume(queue=rabbitmq_queue_name, on_message_callback=lambda ch, method, properties, body: process_license_expiry_message(ch, method, properties, type, body), auto_ack=True)
    print(' [*] Waiting for license expiry messages. To exit press CTRL+C')
    channel.start_consuming()


consume_messages()

while True:
    schedule.run_pending()
    time.sleep(1)
