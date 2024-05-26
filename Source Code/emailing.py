import smtplib
import mimetypes
from email.message import EmailMessage
from flask import Flask, render_template, request

SENDER = "munibsmotiondetector@gmail.com"
PASSWORD = "tfwpusgndjdapldu"

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    email = request.form['email']
    # Process the email as needed
    print(f"Received email: {email}")
    # For demonstration, call Alert function with a sample image
    Alert("path/to/sample_image.jpg", email)
    return f"Email {email} received successfully."

def Alert(image, recipient_email):
    Message = EmailMessage()
    Message["Subject"] = "New customer just showed up"
    Message.set_content("Hey, we just saw a new customer")

    with open(image, "rb") as file:
        content = file.read()

    mime_type, _ = mimetypes.guess_type(image)
    main_type, sub_type = mime_type.split('/')
    Message.add_attachment(content, maintype=main_type, subtype=sub_type)

    gmail = smtplib.SMTP("smtp.gmail.com", 587)
    gmail.ehlo()
    gmail.starttls()
    gmail.login(SENDER, PASSWORD)
    gmail.sendmail(SENDER, recipient_email, Message.as_string())
    gmail.quit()

if __name__ == "__main__":
    app.run(debug=True)
