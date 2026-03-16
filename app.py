# app.py
from flask import Flask, render_template, request, jsonify
import sqlite3
import os
from dotenv import load_dotenv
from groq import Groq

# Load env
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

app = Flask(__name__)

# -----------------------
# Memory / Progress DB
# -----------------------
conn = sqlite3.connect("memory.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS progress(
id INTEGER PRIMARY KEY AUTOINCREMENT,
task TEXT,
status TEXT
)
""")
conn.commit()

def add_progress(task, status="pending"):
    cursor.execute("INSERT INTO progress(task,status) VALUES(?,?)",(task,status))
    conn.commit()

def get_progress():
    cursor.execute("SELECT task,status FROM progress")
    return cursor.fetchall()

# -----------------------
# Tools
# -----------------------
def analyze_profile(profile_text):
    score = 10
    problems = []
    suggestions = []

    if len(profile_text)<120:
        score -= 2
        problems.append("Profile too short")
        suggestions.append("Write 150+ words")
    if "AI" not in profile_text:
        score -=2
        suggestions.append("Mention AI skills")
    if "Python" not in profile_text:
        score -=1
        suggestions.append("Add Python skill")
    return {"score":score,"problems":problems,"suggestions":suggestions}

def generate_gig_ideas():
    return [
        "I will build AI automation for your business",
        "I will create Python automation scripts",
        "I will build custom AI assistants",
        "I will build AI chatbots"
    ]

def skill_gap_analysis():
    return ["API integration","Automation workflows","Chatbot deployment","Web scraping"]

def daily_tasks():
    return ["Improve Fiverr profile","Research 5 competitors","Write first gig","Publish your gig"]

def competitor_analysis(description):
    return {
        "keywords":["AI automation","chatbot","python automation"],
        "suggested_price":"$25-$40",
        "advice":"Start cheaper to get first reviews."
    }

# -----------------------
# Agent logic
# -----------------------
def detect_tool(message):
    m = message.lower()
    if "gig idea" in m:
        return "gig"
    if "skills" in m:
        return "skills"
    if "today" in m:
        return "tasks"
    if "progress" in m:
        return "progress"
    return None

SYSTEM_PROMPT = """
You are a professional freelancing mentor.
Help the user succeed on Fiverr, Upwork, Freelancer.
Tasks:
- analyze profiles
- suggest gigs
- analyze competitors
- recommend skills to learn
- give daily freelancing tasks
If you need info, ask the user to paste it.
"""

def chat(user_message):
    tool = detect_tool(user_message)
    if tool=="gig":
        return "\n".join(generate_gig_ideas())
    if tool=="skills":
        return "\n".join(skill_gap_analysis())
    if tool=="tasks":
        tasks = daily_tasks()
        for t in tasks:
            add_progress(t)
        return "\n".join(tasks)
    if tool=="progress":
        progress = get_progress()
        return "\n".join([f"{t} - {s}" for t,s in progress])

    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[
            {"role":"system","content":SYSTEM_PROMPT},
            {"role":"user","content":user_message}
        ]
    )
    return response.choices[0].message.content

# -----------------------
# Web routes
# -----------------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat_api():
    msg = request.json["message"]
    reply = chat(msg)
    return jsonify({"reply":reply})

if __name__=="__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
