from flask import Flask, Response
from notion_client import Client
from icalendar import Calendar, Event
from datetime import datetime
import os
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

# Initialize Notion client
notion = Client(auth=os.environ["NOTION_API_KEY"])
database_id = os.environ["NOTION_DATABASE_ID"]

def fetch_notion_events():
    try:
        results = notion.databases.query(database_id=database_id).get("results")
        events = []
        for page in results:
            properties = page["properties"]
            title = "Untitled"
            if "Name" in properties and properties["Name"]["title"]:
                title = properties["Name"]["title"][0]["text"]["content"]
            
            start = end = None
            if "Date" in properties and properties["Date"]["date"]:
                start = properties["Date"]["date"]["start"]
                end = properties["Date"]["date"].get("end")
            
            event = {
                "title": title,
                "start": start,
                "end": end,
            }
            events.append(event)
        return events
    except Exception as e:
        app.logger.error(f"Error fetching Notion events: {str(e)}")
        raise

def create_ical(events):
    try:
        cal = Calendar()
        for event in events:
            ical_event = Event()
            ical_event.add("summary", event["title"])
            if event["start"]:
                ical_event.add("dtstart", datetime.fromisoformat(event["start"]))
            if event["end"]:
                ical_event.add("dtend", datetime.fromisoformat(event["end"]))
            cal.add_component(ical_event)
        return cal.to_ical()
    except Exception as e:
        app.logger.error(f"Error creating iCal: {str(e)}")
        raise

@app.route("/calendar.ics")
def serve_calendar():
    try:
        events = fetch_notion_events()
        ical_data = create_ical(events)
        return Response(ical_data, mimetype="text/calendar")
    except Exception as e:
        app.logger.error(f"Error serving calendar: {str(e)}")
        return str(e), 500

@app.route("/")
def hello():
    return "Hello, World! Notion Calendar Sync is running."

@app.route("/env")
def env():
    return f"NOTION_API_KEY: {'Set' if os.environ.get('NOTION_API_KEY') else 'Not Set'}<br>" \
           f"NOTION_DATABASE_ID: {'Set' if os.environ.get('NOTION_DATABASE_ID') else 'Not Set'}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=os.environ.get("PORT", 5000))
