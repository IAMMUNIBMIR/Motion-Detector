import smtplib
import mimetypes
from email.message import EmailMessage

SENDER = "munibsmotiondetector@gmail.com"
PASSWORD = "tfwpusgndjdapldu"

def Alert(recipient_email, image_path):
    print("Sending email to:", recipient_email)
    
    Message = EmailMessage()
    Message["Subject"] = "New customer just showed up"
    Message["From"] = SENDER
    Message["To"] = recipient_email
    Message.set_content("Hey, we just saw a new customer")

    with open(image_path, "rb") as file:
        content = file.read()

    mime_type, _ = mimetypes.guess_type(image_path)
    main_type, sub_type = mime_type.split('/')
    Message.add_attachment(content, maintype=main_type, subtype=sub_type)

    print("Connecting to SMTP server...")
    with smtplib.SMTP("smtp.gmail.com", 587) as gmail:
        gmail.ehlo()
        gmail.starttls()
        
        print("Logging in...")
        gmail.login(SENDER, PASSWORD)
        
        print("Sending email...")
        gmail.send_message(Message)
        
    print("Email sent successfully.")
