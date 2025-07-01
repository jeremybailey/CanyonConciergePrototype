from flask import Flask, request, jsonify, render_template, session
import random
from datetime import datetime
import json
import os
from dotenv import load_dotenv
import openai

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'canyon-dev-secret')  # For session support

# --- Dummy Data ---
EXHIBITIONS = [
    {"title": "Reflections in Real Time", "desc": "18 minutes of gorgeous glitch.", "gallery": 3},
    {"title": "Neon Aftermath", "desc": "Immersive light and sound.", "gallery": 1},
    {"title": "Postmodern Picnic", "desc": "Edible installations. Yes, really.", "gallery": 2},
]
MENU = [
    {"item": "Matcha Cloud Latte", "desc": "Frothy, dreamy, green."},
    {"item": "Pixel Croissant", "desc": "Flaky, meta, delicious."},
    {"item": "Glitch Salad", "desc": "Looks wrong, tastes right."},
]
EVENTS = [
    {"name": "Artist Q&A: Ada Loop", "time": "2:00 PM", "location": "Auditorium"},
    {"name": "Live Coding Demo", "time": "4:00 PM", "location": "Gallery 3"},
]

# --- Helper Functions ---
def get_greeting(name=None):
    base = random.choice([
        "Welcome to Canyon!",
        "Hey there — you made it!",
        "Hello from your Canyon Concierge",
        "Art and algorithms await!",
    ])
    if name:
        base = f"{base} {name},"
    return base

def suggest_exhibition():
    ex = random.choice(EXHIBITIONS)
    return f"*{ex['title']}* — {ex['desc']} (Gallery {ex['gallery']})"

def suggest_menu():
    item = random.choice(MENU)
    return f"{item['item']}: {item['desc']}"

def suggest_event():
    event = random.choice(EVENTS)
    return f"{event['name']} at {event['time']} in {event['location']}"

def get_bathroom_info():
    return "🚻 Nearest washrooms are just past Gallery 1. Here’s a map 🗺️ 👉 https://canyon.fake/bathrooms"

# --- Custom Knowledge Loader ---
def load_custom_knowledge():
    path = os.path.join(os.path.dirname(__file__), 'custom_knowledge.json')
CHECKOUT_LINK = "https://canyon.fake/checkout"
PURCHASE_KEYWORDS = [
    "buy ticket", "purchase ticket", "admission", "buy admission",
    "get tickets", "purchase pass", "order food", "menu item", "buy", "purchase"
]

def append_checkout_link_if_needed(reply):
    lower_reply = reply.lower()
    if any(keyword in lower_reply for keyword in PURCHASE_KEYWORDS):
        if CHECKOUT_LINK not in reply:
            reply = f'{reply}\n\n<a href="{CHECKOUT_LINK}" target="_blank">Buy now</a>'
    return reply

def openai_fallback(user_msg, user_name=None):
    if not OPENAI_API_KEY:
        return None
    import time
    ASSISTANT_ID = "asst_S2QbfA9NqgXKgZ8iymO1TjuG"
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        # Personalize user message if user_name is present
        if user_name:
            user_msg = f"Visitor name: {user_name}.\n" + user_msg
        # Inject current local time for all queries
        import datetime
        now = datetime.datetime.now().strftime("%A, %B %d, %Y at %H:%M")
        user_msg += f"\n\nCurrent local time is {now}."
        # Create a thread for the conversation (stateless for now)
        thread = client.beta.threads.create()
        thread_id = thread.id
        # Add user message
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=user_msg
        )
        # Run the assistant
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=ASSISTANT_ID
        )
        # Poll for completion
        while run.status not in ["completed", "failed"]:
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
        if run.status == "completed":
            messages = client.beta.threads.messages.list(thread_id=thread_id)
            # Return the latest assistant message
            for msg in messages.data:
                if msg.role == "assistant":
                    reply = msg.content[0].text.value.strip()
                    # Post-process to remove RAG citation artifacts
                    import re
                    # Remove patterns like 4:0†filename.json】, numbers:filename.json, etc.
                    reply = re.sub(r"\d+:\d+†[\w_.-]+\.json】?", "", reply)
                    # Do NOT remove \d+:\d+ patterns (to preserve times like 9:00PM)
                    reply = re.sub(r"[\w_.-]+\.json", "", reply)  # Remove any .json file references
                    reply = re.sub(r"†", "", reply)  # Remove stray daggers
                    # Remove any text inside 【 ... 】 brackets (including the brackets)
                    reply = re.sub(r"【[^】]*】", "", reply)
                    reply = re.sub(r"\s+", " ", reply).strip()  # Normalize whitespace
                    # Remove any trailing or standalone '【', '】', or '【.' at the end
                    reply = re.sub(r"[【】.]+$", "", reply).strip()
                    # Append checkout link if relevant
                    reply = append_checkout_link_if_needed(reply)
                    return reply
        return None
    except Exception as e:
        import traceback
        print("[OPENAI ERROR]", e)
        traceback.print_exc()
        return None

# --- Main Route ---
@app.route('/sms', methods=['POST'])
def sms_reply():
    user_msg = request.json.get('Body', '').strip().lower()
    user_name = request.json.get('User', None)
    # Simulate memory of previous visits
    visited = request.json.get('Visited', False)

    if user_msg in ['stop', 'leave me alone']:
        return jsonify({"reply": "Understood. I’ll step back. If you need me, just text again. 🌙"})

    if any(x in user_msg for x in ["bathroom", "restroom", "toilet"]):
        return jsonify({"reply": get_bathroom_info()})
    if any(x in user_msg for x in ["how do i get", "directions", "address", "where is canyon", "get to canyon", "find canyon", "location"]):
        return jsonify({"reply": (
            "🗺️ Canyon is at 456 Postmodern Ave, New York, NY 10013.\n"
            "Here’s a map: https://goo.gl/maps/xyzCanyon\n"
            "Subway: Canal St (A/C/E/N/Q/R/6).\n"
            "If you get lost, just text me—I’ll send a poetic rescue squad."
        )})




    if "hello" in user_msg or "hi" in user_msg or "hey" in user_msg:
        greeting = get_greeting(user_name)
        if visited:
            greeting += " (Welcome back!)"
        return jsonify({"reply": greeting})

    # Custom knowledge check
    # OpenAI fallback
    ai_reply = openai_fallback(user_msg, user_name)
    if ai_reply:
        return jsonify({"reply": ai_reply})
    # Default poetic fallback
    reply = random.choice([
        "I’m here if you need directions, recs, or a little art wisdom. ✨",
        "Lost in the gallery? I can help — or at least keep you company.",
        "Ask me anything — from bathroom locations to the meaning of postmodernism.",
        "Need a food rec, event tip, or existential reassurance? I’m your bot!"
    ])
    return jsonify({"reply": reply})

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/reset_session', methods=['POST'])
def reset_session():
    session.clear()
    return jsonify({'success': True})

@app.route('/webchat', methods=['POST'])
def webchat():
    # Use Flask session to remember user's name
    user_msg = request.json.get('Body', '').strip()
    visited = request.json.get('Visited', False)
    user_name = session.get('user_name', None)
    lower_msg = user_msg.lower()

    # Only run name extraction if user_name is not already set
    if not user_name:
        import re
        NON_NAMES = {"in", "at", "here", "there", "gallery", "the", "a", "an", "museum", "visitor", "i", "me", "you", "we", "us", "on", "to", "for", "and", "but", "or", "with", "from", "of", "is", "am", "are", "my", "your", "call", "it", "this", "that", "yes", "no", "thanks", "thank", "hi", "hello", "hey"}

        name_pattern = re.compile(r"(?:my name is|i'm|i am|call me)\s+([a-zA-Z][a-zA-Z\-']{1,19})(?:\s+([a-zA-Z][a-zA-Z\-']{1,19}))?", re.IGNORECASE)
        match = name_pattern.search(user_msg)
        plausible_name = None
        if match:
            first = match.group(1)
            second = match.group(2)
            plausible_name = first
            if second:
                plausible_name += f" {second}"
        elif session.get('asked_name', False):
            words = user_msg.strip().split()
            if 1 <= len(words) <= 2 and all(w.isalpha() and w.lower() not in NON_NAMES for w in words):
                plausible_name = ' '.join([w.capitalize() for w in words])
        if plausible_name:
            name_words = [w.lower() for w in plausible_name.split()]
            if all(w not in NON_NAMES for w in name_words) and 2 <= len(plausible_name) <= 20:
                session['user_name'] = plausible_name
                user_name = plausible_name
                session.pop('asked_name', None)
                return jsonify({"reply": f"Nice to meet you, {user_name}! How can I help?"})
            else:
                # Don't set user_name or clear asked_name if invalid
                return jsonify({"reply": "Sorry, I didn't catch your name. What should I call you?"})
        # If no name, ask for it
        session['asked_name'] = True
        return jsonify({"reply": "Hi! What should I call you? 😊"})

    # Only respond with greeting for explicit greeting messages
    if lower_msg.strip() in ["hello", "hi", "hey"]:
        greeting = get_greeting(user_name)
        if visited:
            greeting += " (Welcome back!)"
        return jsonify({"reply": greeting})

    # All other messages go to the AI or bathroom info
    if lower_msg in ['stop', 'leave me alone']:
        return jsonify({"reply": "Understood. I’ll step back. If you need me, just text again. 🌙"})
    if any(x in lower_msg for x in ["bathroom", "restroom", "toilet"]):
        return jsonify({"reply": get_bathroom_info()})
    ai_reply = openai_fallback(user_msg, user_name)
    if ai_reply:
        return jsonify({"reply": ai_reply})
    # No fallback: always return OpenAI Assistant response or a minimal error
    return jsonify({"reply": "Sorry, I couldn't get a response from the AI right now."})

import traceback

@app.errorhandler(Exception)
def handle_exception(e):
    print('[GLOBAL ERROR]', e)
    traceback.print_exc()
    return jsonify({'reply': 'Sorry, something went wrong on my end. The bot is having an existential moment. 🌀'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5050)
