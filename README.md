 Hackathon Progress Tracker

    A web app to track your team's progress across multiple hackathons. 

    Features
    - 🔐 Passcode-protected dashboard 
	- Live Devpost feed 
    - 📊 Visual progress bars with rainbow gradient animation
    - ✏️ Add hackathons with name, date, and description
    - 📈 Accumulative progress updates (adds to current percentage)
    - 📝 Side notes history for each progress change
    - 🗑️ Delete hackathons
    - 📥 CSV export for data backup

    Tech Stack
    - Flask (Python web framework)
    - Vanilla HTML/CSS/JavaScript
    - JSON file storage

    Usage
    1. Start the server: python app.py
    2. Open http://localhost:80 in browser
    3. Enter passcode
    4. Add hackathons and track progress

    Layout
    Each hackathon displays:
    - Left side: Name, percentage, progress bar, update form
    - Right side: Grey description tile (optional)
    - Below: Notes history
