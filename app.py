from flask import Flask, request, jsonify, render_template
import sqlite3
import os
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

# Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

app = Flask(__name__)

# -----------------------
# DATABASE (Memory)
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
    cursor.execute("INSERT INTO progress(task,status) VALUES(?,?)", (task, status))
    conn.commit()

def get_progress():
    cursor.execute("SELECT task,status FROM progress")
    return cursor.fetchall()

# -----------------------
# TOOLS
# -----------------------
def generate_gig_ideas():
    return [
        "I will build AI automation for your business",
        "I will create Python automation scripts",
        "I will build custom AI assistants",
        "I will build AI chatbots"
    ]

def skill_gap_analysis():
    return [
        "API integration",
        "Automation workflows",
        "Chatbot deployment",
        "Web scraping"
    ]

def daily_tasks():
    return [
        "Improve Fiverr profile",
        "Research 5 competitors",
        "Write your first gig",
        "Publish your gig"
    ]

# -----------------------
# TOOL DETECTION
# -----------------------
def detect_tool(message):
    m = message.lower()

    if "gig" in m:
        return "gig"
    if "skill" in m:
        return "skills"
    if "today" in m or "task" in m:
        return "tasks"
    if "progress" in m:
        return "progress"

    return None

# -----------------------
# AI SYSTEM PROMPT
# -----------------------
SYSTEM_PROMPT = """
You are a professional freelancing mentor.

Help the user succeed on Fiverr, Upwork, Freelancer.

Be clear, practical and helpful.
"""

# -----------------------
# CHAT FUNCTION
# -----------------------
def chat(user_message):

    tool = detect_tool(user_message)

    try:
        if tool == "gig":
            return "\n".join(generate_gig_ideas())

        if tool == "skills":
            return "\n".join(skill_gap_analysis())

        if tool == "tasks":
            tasks = daily_tasks()
            for t in tasks:
                add_progress(t)
            return "\n".join(tasks)

        if tool == "progress":
            progress = get_progress()
            if not progress:
                return "No progress yet."
            return "\n".join([f"{t} - {s}" for t, s in progress])

        # AI Response
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ]
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"Error: {str(e)}"

# -----------------------
# ROUTES
# -----------------------
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat_api():
    try:
        data = request.get_json()

        if not data or "message" not in data:
            return jsonify({"reply": "Invalid request"}), 400

        user_message = data["message"]

        reply = chat(user_message)

        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"reply": f"Server error: {str(e)}"}), 500


# -----------------------
# RUN SERVER
# -----------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
