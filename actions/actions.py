import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from rasa_sdk import Action
from rasa_sdk.events import SlotSet
from datetime import datetime

# Google Classroom API scope
SCOPES = ['https://www.googleapis.com/auth/classroom.courses.readonly', 'https://www.googleapis.com/auth/classroom.coursework.me']

# Function to authenticate with Google Classroom
def authenticate_gclassroom():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                raise FileNotFoundError("The 'credentials.json' file is missing. Please place it in the root directory of your project.")
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            flow.redirect_uri = 'http://localhost:8080/'
            creds = flow.run_local_server(port=8080)

        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('classroom', 'v1', credentials=creds, cache_discovery=False)
    return service

# Fetch courses from Google Classroom
def get_courses(service):
    results = service.courses().list().execute()
    courses = results.get('courses', [])
    return courses


# Rasa custom action to fetch courses
class ActionFetchCourses(Action):
    def name(self) -> str:
        return "action_fetch_courses"

    def run(self, dispatcher, tracker, domain):
        service = authenticate_gclassroom()
        courses = get_courses(service)
        if courses:
            course_names = "\n".join([course['name'] for course in courses])
            dispatcher.utter_message(text=f"Your courses are:\n{course_names}")
            return [SlotSet("courses", course_names)]
        else:
            dispatcher.utter_message(text="You don't have any courses.")
            return [SlotSet("courses", "")]

class ActionAskForTime(Action):
    def name(self) -> str:
        return "action_ask_for_time"

    def run(self, dispatcher, tracker, domain):
        current_time = datetime.now().strftime("%H:%M:%S")
        dispatcher.utter_message(text=f"The current time is {current_time}.")
        return [SlotSet("time", current_time)]