# An example of a Philips Hue and Google Calendar integration
My Work-from-Home "office" is in a dark corner of my house, I wanted a way to keep track of time and also look well lit in video calls. My solution was to get the [Philips Hue Light Bar](https://www2.meethue.com/en-us/p/hue-white-and-color-ambiance-play-light-bar-double-pack/7820230U7) and write a program to control the lights based off of events in my calendar. Check out a [video of the experience](https://youtu.be/GQiMuCmbtgM).

## Requirements
Hue Python API, I'm using [Qhue](https://github.com/quentinsf/qhue) to make interactions with the Bridge easier (see that project for installation instructions).

Enable the [Google Calendar API](https://developers.google.com/calendar/quickstart/python) for your Google account and install the client library. Reference the [Python Calendar API](https://developers.google.com/resources/api-libraries/documentation/calendar/v3/python/latest/index.html) as needed.

[Hue Lights API](https://developers.meethue.com/develop/hue-api/lights-api/) (you will to sign up for a developer account to access) to understand what's available.

## To get it working
Go through the [Get Started](https://developers.meethue.com/develop/get-started-2/) page on the Hue Developers site to use the CLIP API Debugger to register a new username. Replace the BRIDGE_IP and BRIDGE_USERNAME variables in the script, update the LOGGING variable as necessary and execute with:
```
python work_lights.py
```

If you want to run it as a background process, set LOGGING to False and run with
```
python work_lights.py &
```
