from __future__ import print_function
from datetime import timedelta
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from qhue import Bridge
from qhue import QhueException

import datetime
import os.path
import pickle
import yaml
import random
import time

# End program at specific military time
WORK_DAY_END = datetime.time(16, 30, 00)

# Allow printing to STDOUT
LOGGING = True

# Philips Hue Bridge details
BRIDGE_IP = '1.1.1.1'  # Update with your Bridge's IP address
BRIDGE_USERNAME = 'username'  # Update with your Bridge's username
LIGHTS = [1, 2] # Update with your light's IDs

# How often to update the lights
LIGHT_CHANGE_INTERVAL_MIN = 4
LIGHT_CHANGE_INTERVAL_SEC = LIGHT_CHANGE_INTERVAL_MIN * 60

# How many minutes before the event to switch to GVC mode
# Should be larger than LIGHT_CHANGE_INTERVAL_MIN
CAL_EVENT_CHECK_INTERVAL_MIN = 5

with open('config.yaml') as config_file:
    config = yaml.load(config_file, Loader=yaml.FullLoader)
    if 'BRIDGE_IP' in config:
        BRIDGE_IP = config['BRIDGE_IP']
    if 'BRIDGE_USERNAME' in config:
        BRIDGE_USERNAME = config['BRIDGE_USERNAME']

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def TurnOnLights(lights):
  try:
    [lights(light, 'state') for light in LIGHTS]
  except QhueException as err:
    if LOGGING:
      print('Turning lights on')
    [lights(light, 'state', on=True) for light in LIGHTS]


def TurnOffLights(lights):
  [lights(light, 'state', on=False) for light in LIGHTS]


def SetAmbientColor(lights):
  x = round(random.random(), 3)
  y = round(random.random(), 3)

  [lights(light, 'state', xy=[x, y], bri=254, transitiontime=100)
          for light in LIGHTS]
  if LOGGING:
    print('x={}, y={} @ {}'.format(x, y, datetime.datetime.now()))
  return


def SetGVCColor(lights):
  [lights(light, 'state', xy=[0.300, 0.300], bri=254)
          for light in LIGHTS]
  return


def GetCalendarEvents(service):
  now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
  if LOGGING:
    print('Getting events...')
  try:
    events_result = service.events().list(calendarId='primary', timeMin=now,
                                          maxResults=3, singleEvents=True,
                                          orderBy='startTime').execute()
  except ConnectionResetError as err:
    print('Caught ConnectionResetError!')
    time.sleep(60)
    GetCalendarEvents(service)

  events = events_result.get('items', [])
  if not events:
    if LOGGING:
      print('No upcoming events found.')

  for event in events:
    event_start_datetime_str = event['start']['dateTime']
    event_start_date_obj = datetime.datetime.strptime(
        event_start_datetime_str[:19], '%Y-%m-%dT%H:%M:%S')
    event_end_datetime_str = event['end']['dateTime']
    event_end_date_obj = datetime.datetime.strptime(
        event_end_datetime_str[:19], '%Y-%m-%dT%H:%M:%S')
    attendees = event.get('attendees')
    
    # Only want events that have reminders set
    if event['reminders']['useDefault']:
      # If I'm an attendee and I've accepted the invitation
      if attendees:
        for me in attendees:
          if me.get('self') and me.get('responseStatus') == 'accepted':
            if LOGGING:
              print('Attending event: {}'.format(event['summary']))
            return EventNotify(event_start_date_obj, event_end_date_obj)
      
      # If I'm the creator of the event and I've enabled it to remind me
      if event['creator'].get('self'):
        if LOGGING:
          print('Self-organized event: {}'.format(event['summary']))
        return EventNotify(event_start_date_obj, event_end_date_obj)
  return 'Ambient'
    

def EventNotify(event_start_date_obj, event_end_date_obj):
  now_obj = datetime.datetime.now()
  now_plus_minutes_obj = datetime.datetime.now() + timedelta(
      minutes=CAL_EVENT_CHECK_INTERVAL_MIN)
  starting_soon = (event_start_date_obj > now_obj and
                   event_start_date_obj < now_plus_minutes_obj)
  in_progress = (event_start_date_obj < now_obj and
                 event_end_date_obj > now_obj)
  if LOGGING:
    print ('now_obj: {}'.format(now_obj))
    print ('now_plus_minutes_obj: {}'.format(now_plus_minutes_obj))
    print ('event_start_date_obj: {}'.format(event_start_date_obj))
    print ('event_end_date_obj: {}'.format(event_end_date_obj))
    print ('starting_soon: {}'.format(starting_soon))
    print('in_progress: {}'.format(in_progress))
  if (starting_soon or in_progress):
    if LOGGING:
      print('GVC')
    return 'GVC'
  else:
    if LOGGING:
      print('Ambient')
    return 'Ambient'


def main():
  # https://developers.google.com/calendar/quickstart/python
  # Initialize Calendar API
  creds = None
  if os.path.exists('token.pickle'):
    with open('token.pickle', 'rb') as token:
      creds = pickle.load(token)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
              'credentials.json', SCOPES)
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open('token.pickle', 'wb') as token:
      pickle.dump(creds, token)
  
  service = build('calendar', 'v3', credentials=creds)
  
  # https://developers.meethue.com/develop/hue-api/lights-api/
  # https://github.com/quentinsf/qhue
  # Initialize Philips Hue Bridge
  bridge = Bridge(BRIDGE_IP, BRIDGE_USERNAME)
  lights = bridge.lights
  
  now_time = datetime.datetime.now().time()
  
  if now_time < WORK_DAY_END:
    TurnOnLights(lights)
  
  while now_time < WORK_DAY_END:
    
    # Identify if there is a GVC coming up or not
    event_type = GetCalendarEvents(service)
  
    if event_type == 'GVC':
      SetGVCColor(lights)

    elif event_type == 'Ambient':
      SetAmbientColor(lights)

    if LOGGING:
      print('Sleeping for {} seconds \n'.format(LIGHT_CHANGE_INTERVAL_SEC))
    time.sleep(LIGHT_CHANGE_INTERVAL_SEC)
    now_time = datetime.datetime.now().time()

  print('You are done working, now go play!')
  TurnOffLights(lights)


if __name__ == '__main__':
    main()
