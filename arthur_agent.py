from google import genai
from google.genai import types
from dotenv import load_dotenv
from imap_tools import MailBox, A
import os
import smtplib
from email.mime.text import MIMEText

load_dotenv()

email = os.getenv("EMAIL")
email_password = os.getenv("EMAIL_PASSWORD")

keys = [
     os.getenv("MY_API_KEY_1"),
     os.getenv("MY_API_KEY_2"),
     os.getenv("MY_API_KEY_3"),
     os.getenv("MY_API_KEY_4")
]

for key in keys:
     try:
          temp_key = genai.Client(api_key=key)
          response = temp_key.models.generate_content(
               model="gemini-2.5-flash",
               contents="hi"
          )
          if response and response.text:
               print("working_key_found")
               client = temp_key
               model = "gemini-2.5-flash-lite"
               break
     except Exception as e:
          print(f"faild key:")
          continue

chat_history = []

with open("system_prompt.txt") as f:
    system_prompt = f.read()

def email_read(seen: bool ,limit: int) -> str:
     email_box = []
     with MailBox("imap.gmail.com").login(email, email_password) as mailbox:
          for msg in mailbox.fetch(A(seen=seen), limit=limit, reverse=True):
               text_email = (f"---Emails---\n"
                             f"From: {msg.from_}\n"
                              f"Subject: {msg.subject}\n"
                              f"Body: {msg.text}\n"
                              f"Date: {msg.date}\n"
                              )
               email_box.append(text_email)
          return "\n".join(email_box) if email_box else "No emails found."
     
def send_email(to_email: str, message: str) -> str:
     """
     Sends an email to a specified recipient.
     args:
          to_email (str): The recipient's email address.
          message (str): The content of the email to be sent.
     """
     try:
          msg = MIMEText(message)
          msg["Subject"] = "Arthur Email"
          msg["From"] = email
          msg["To"] = to_email
          server = smtplib.SMTP("smtp.gmail.com", 587)
          server.starttls()
          server.login(email, email_password)
          server.sendmail(email, to_email, msg.as_string())
          server.quit()
          return f"Success: Email successfully sent to {to_email}."
     except Exception as e:
          return f"Failed to send email.\nReason: {e}"

tools = [email_read, send_email]

def execute_tool(tool_name, args):
     function_tool = {"email_read": email_read,
                      "send_email": send_email
                      }

     if tool_name not in function_tool:
          return f"Unknown tool: {tool_name}"
     try:
          tool_function = function_tool[tool_name]
          return tool_function(**args)
     except Exception as e:
          return f"Tool execution error: {e}"

def Arthur_brain(user_input):
     try:
            
          config = types.GenerateContentConfig(
          system_instruction=system_prompt,
          tools=tools)

          chat_history.append({"role":"user", "parts":[{"text":user_input}]})

          response = client.models.generate_content(
                model=model,
                config=config,
                contents=chat_history
          )

          while response.function_calls:
               for call in response.function_calls:
                    tool_result = execute_tool(
                           call.name,
                           call.args
                    )

                    chat_history.append({"role":"model",
                                         "parts":[{"function_call":{"name": call.name,
                                                                    "args": call.args}}]})
                    
                    chat_history.append({
                         "role":"tool",
                         "parts": [{str(tool_result)}]}
               )

               response = client.models.generate_content(
                    model=model,
                    config=config,
                    contents=chat_history
               )

          arthur = response.text
          chat_history.append({"role":"model", "parts":[{"text":arthur}]})
          return f"Arthur: {arthur}"

     except Exception as e:
          return f"error: {e}"

while True:
     user = input("you: ")
     if user.lower().strip() == "exit":
          print(Arthur_brain(user))
          break
     process = Arthur_brain(user)
     print(process)

