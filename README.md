# Canyon Concierge Prototype

This is a prototype of the Canyon Concierge — an SMS-based AI guide for Canyon, a next-generation media art museum in New York.

## Features
- Friendly, poetic, and witty AI persona
- Handles all visitor needs via SMS (no app downloads)
- Remembers returning guests (simulated)
- Recommends art, food, events, and logistics
- Short, expressive messages with emoji, links, and maps

## How to Run
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the server:
   ```bash
   python app.py
   ```
3. Simulate SMS by sending POST requests to `/sms` with JSON payloads like:
   ```json
   {"Body": "What's on today?", "User": "Alex", "Visited": true}
   ```

---

This prototype uses dummy data for events, exhibitions, and menu items. Replace with live data as needed.
