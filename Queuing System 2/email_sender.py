# email_sender.py
import zmq
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader
from database_checker import license_data

host = "smtp-mail.outlook.com"
port = 587
user = "abdulellah.n16@outlook.com"
password = "Q@5mk8wk"
email_from = "abdulellah.n16@outlook.com"
template_dir = ""

context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://127.0.0.1:5555")  # Bind to localhost on port 5555

# Process license data and send emails
for C_email, idclients, expiry_date in license_data:
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
    with smtplib.SMTP(host, port) as server:
        server.starttls()
        server.login(user, password)
        server.sendmail(email_from, C_email, message.as_string())

    # Send a message via ZeroMQ
    zmq_message = f"License {idclients} will expire on {expiry_date}. Email notification sent to {C_email}"
    socket.send_string(zmq_message)
    print(f"Sent message: {zmq_message}")

# Close ZeroMQ and its context
socket.close()
context.term()
