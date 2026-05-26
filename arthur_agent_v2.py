from google import genai
from google.genai import types
import os
from dotenv import load_dotenv
from datetime import date, datetime, time
import inspect
from ollama import chat
import webbrowser
import json
import pyautogui
import pyttsx3
from imap_tools import MailBox
from imap_tools import A
import smtplib
from email.message import EmailMessage
import sounddevice as sd

load_dotenv()
API_KEYS = [os.getenv("MY_API_KEY_1"),
            os.getenv("MY_API_KEY_2"),
            os.getenv("MY_API_KEY_3"),
            os.getenv("MY_API_KEY_4")]

email = os.getenv("EMAIL")
email_password = os.getenv("EMAIL_PASSWORD")

key_index = 0
client = genai.Client(api_key=API_KEYS[key_index])
chat_memory = []

def open_website(name: str) -> str:
    if not os.path.exists("website_link.json"):
        return f"website file not found"
    with open("website_link.json", "r") as f:
        link = json.load(f)
        name = name.lower()
        if name in link:
            webbrowser.open(link[name])
            return f"{name} link open"
        else:
            return f"website link not found: {name}"


def switch_keys():
    global client, key_index
    key_index += 1
    if key_index >= len(API_KEYS):
        return False
    client = genai.Client(api_key=API_KEYS[key_index])
    return True

with open("system_prompt.txt") as f:
    system_prompt = f.read()

def date_time():
    time = datetime.now().strftime("%H:%M:%S")
    current_date = date.today().strftime("%d-%m-%Y")
    return f"Current_time: ({time}) | Current_date: ({current_date})"


def open_system_app(name: str)-> str:
    try:
        pyautogui.hotkey("winleft", "s")
        pyautogui.write(name, interval=0.05)
        pyautogui.press("enter")

        return"success"
    except Exception as e:
        return "faield"
    
def speak(word):
    engine = pyttsx3.init()
    engine.say(word)
    engine.runAndWait()

def read_email(seen: bool, limit: int)-> str:
    emails = []
    try:
        with MailBox("imap.gmail.com").login(email, email_password) as mailbox:
            for msg in mailbox.fetch(A(seen=seen), limit=limit, reverse=True):
                text = (f"---Emails---\n"
                        f"From: {msg.from_}\n"
                        f"Subject: {msg.subject}\n"
                        f"Body: {msg.text}\n"
                        f"Date: {msg.date}\n")
                emails.append(text)
            return "\n".join(emails) if emails else "No email found"
    except Exception as e:
        return "something not write"
    
def send_email(to: str, subject: str, body: str)-> str:
    try:
        msg = EmailMessage()
        msg["From"] = email
        msg["to"] = to
        msg["Subject"] = subject
        msg.set_content(body)
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(email, email_password)
            server.send_message(msg)
        return f"Email sent successfully to {to}"
    except Exception as e:
        return f"Failed to send email: {e}"

tools = [date_time, open_website, open_system_app, read_email, send_email,]

def tool_run(name, args):
    function_name = {"date_time":date_time,
                     "open_website": open_website,
                     "open_system_app": open_system_app,
                     "read_email": read_email,
                     "send_email": send_email}
    if name not in function_name:
        return f"Unknown tool name {name}"
    try:
        function_name = function_name[name]
        sig = inspect.signature(function_name)
        clean_args = {k: v for k, v in args.items()
                      if k in sig.parameters}
        return function_name(**clean_args)
    except Exception as e:
        return f"tool execution error: {e}"

def model(user_input):

    global client

    chat_memory.append({"role":"user", "parts":[{"text":user_input}]})

    config = types.GenerateContentConfig(system_instruction=system_prompt,
                                         tools=tools)

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            config=config,
            contents=chat_memory
        )
        if not response.function_calls:
            arthur = response.text
            chat_memory.append({"role":"model",
                            "parts": [{"text":arthur}]})
            return f"Arthur: {arthur}"
        
        max_call = 5
        tool_call = 0

        while response.function_calls and tool_call < max_call:
            tool_call += 1
            for call in response.function_calls:
                function_name = call.name
                arguments = call.args
                result = tool_run(function_name, arguments)

                chat_memory.append({
                    "role": "tool",
                    "parts": [{
                        "function_response":{"name": function_name,
                                             "response":{"result": result}}
                    }]
                })
                
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                config=config,
                contents=chat_memory
            )
        arthur = response.text
        chat_memory.append({"role":"model",
                           "parts": [{"text":arthur}]})
        return f"Arthur: {arthur}"
    
    except Exception as e:
        if "429" in str(e):
            if switch_keys():
                return model(user_input)
            
            return "All API keys exhausted (rate limit reached)"
        return f"Error: {e}"
    
def local_arthur(user_input):
    message = [{"role":"user",
                "content":user_input}]
    
    response = chat(model="llama3.2:3b",
                    messages=message
                    )
    return response.message.content

while True:
    user = input("you: ")
    if user == "exit":
        print("Goodbye")
        break
    if not user:
        continue
    response = model(user)
    print(response)
    speak(response)
    if "All API keys exhausted (rate limit reached)" in response:
        print("All API keys exhausted.")
        print("Local Arthur activated.")
        print("Type 'api' to retry Main Arthur.")
        print("Type 'exit' to quit.")
        while True:
            user = input("you: ")
            if user == "api":
                break
            if user == "exit":
                print(local_arthur(user))
                break
            else:
                response = local_arthur(user)
            print(response)

# while True:
#     user = listen()
#     print("you:", user)
#     rp = local_arthur(user)
#     print(rp)