import mysql.connector
import zmq
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader

host = "localhost"
user = "root"
password = "Q@5mk8wK"
database = "dba"
port = 3307

email_host = "smtp-mail.outlook.com"
email_port = 587
email_user = "abdulellah.n16@outlook.com"
email_password = "Q@5mk8wk"
email_from = "abdulellah.n16@outlook.com"

template_dir = ""

context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://127.0.0.1:5555")  # Bind to localhost on port 5555

try:
    connection = mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database,
        port=port
    )

    if connection.is_connected():
        print("Connected to the database")

        # Fetch licenses that will expire in 2 weeks or less
        cursor = connection.cursor()
        query = "SELECT C_email, idclients, Expiry_date FROM clients WHERE Expiry_date <= (NOW() + INTERVAL 2 WEEK)"
        cursor.execute(query)
        results = cursor.fetchall()

        for C_email, idclients, expiry_date in results:
            # Load Jinja2 template
            env = Environment(loader=FileSystemLoader(template_dir))
            template = env.get_template("email_template.html")

            # Render the template with client details
            email_body = template.render(idclients=idclients, expiry_date=expiry_date)

            # Create the MIME object
            message = MIMEMultipart()
            message['From'] = email_from
            message['To'] = C_email
            message['Subject'] = "License Renewal Reminder"
            message.attach(MIMEText(email_body, 'html'))

            # Connect to the SMTP server and send the email
            with smtplib.SMTP(email_host, email_port) as server:
                server.starttls()
                server.login(email_user, email_password)
                server.sendmail(email_from, C_email, message.as_string())

            # Send a message via ZeroMQ
            zmq_message = f"License {idclients} will expire on {expiry_date}. Email notification sent to {C_email}"
            socket.send_string(zmq_message)
            print(f"Sent message: {zmq_message}")

except mysql.connector.Error as err:
    print(f"MySQL Error: {err}")

except smtplib.SMTPException as smtp_err:
    print(f"SMTP Error: {smtp_err}")

finally:
    if 'connection' in locals() and connection.is_connected():
        connection.close()
        print("Connection closed")

socket.close()
context.term()
