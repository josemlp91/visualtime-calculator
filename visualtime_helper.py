import logging
import json
import requests
import hashlib
import pytz

import os, time
from datetime import date, datetime, timedelta
from datetime import datetime


class VisualTimeHelper:

    def __init__(self, username, password):
        
        os.environ['TZ'] = 'Europe/Madrid'
        time.tzset()
        
        self.base_url = "https://zerows.azurewebsites.net"
        self.headers = {
            'Sec-Fetch-Mode': 'cors',
            'Origin': 'https://zero.visualtime.net',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36',
            'Access-Control-Allow-Methods': 'POST, GET, PUT, OPTIONS, DELETE',
            'Content-Type': 'application/json; charset=utf-8',
            'Access-Control-Allow-Origin': '*',
            'Accept': 'application/json',
            'Referer': 'https://zero.visualtime.net/',
            'Access-Control-Allow-Headers': 'Access-Control-Allow-Methods, Access-Control-Allow-Origin, Origin, X-Requested-With, Content-Type, Accept',
        }

        self.username = username
        self.password = hashlib.md5(password.encode()).hexdigest()

        self.token = None
        self.user_id = None

        # os.environ['TZ'] = 'Europe/Madrid'
        # time.tzset()

    def login(self):

        login_url = self.base_url + "/users/authenticate"
        login_data = {"username": self.username, "password": self.password}
        response = requests.post(login_url, headers=self.headers, data=json.dumps(login_data))

        if response.status_code != 200:
            return response.text

        json_response = response.json()

        self.token = json_response.get('token')
        self.user_id = json_response.get('id')
        self.headers['Authorization'] = f"Bearer {self.token}"

    def get_balance(self):
        balance_url = self.base_url + f"/api/accruals//{self.user_id}"
        response = requests.get(balance_url, headers=self.headers)
        try:
            balance = response.json()
        except:
            return 0

        try:
            balance_minutes = balance['item1'][3]['value']
        except:
            return 0

        return timedelta(minutes=balance_minutes)

    def get_output_time(self, work_hours=None, work_minutes=None):
        today = date.today()
        str_today = today.strftime("%Y%m%d")
        shedule_url = self.base_url + f"/api/punches/GetEmployeePunchesBetweenDates/{self.user_id}/{str_today}/{str_today}"
        response = requests.get(shedule_url, headers=self.headers)
        try:
            puches = response.json()
        except:
            return 0

        input_times = []
        output_times = []

        last_direction = 2
        for push in puches:
            if push.get('deleted'):
                continue

            last_direction = push.get('direction')
            if last_direction == 1:
                input_times.append(datetime.strptime(push.get('dateTime')[0:19], '%Y-%m-%dT%H:%M:%S'))
            elif last_direction == 2:
                output_times.append(datetime.strptime(push.get('dateTime')[0:19], '%Y-%m-%dT%H:%M:%S'))

        if not work_hours or not work_minutes:
            if len(input_times):
                daily_time = puches[0].get('tag').split(":")
                try:
                    work_hours = int(daily_time[1])
                    work_minutes = int(daily_time[2])
                except:
                    work_hours = 7
                    work_minutes = 0
            else:
                work_hours = 7
                work_minutes = 40


        if len(input_times) - len(output_times) == 1:
            output_times.append(datetime.now())

        if len(input_times) != len(output_times):
            return {"error": "Input puches dont match with output puches."}

        time_diff_acumulator = []
        for i, time in enumerate(input_times):
            time_diff = output_times[i] - input_times[i]
            time_diff_acumulator.append(time_diff.seconds)


        min_daily_working_seconds = (work_hours * 60 * 60) + (work_minutes * 60)
        working_seconds = sum(time_diff_acumulator)
        diff_working_seconds = min_daily_working_seconds - working_seconds
        now = datetime.now()

        output_time = now + timedelta(seconds=diff_working_seconds)
        balance = self.get_balance()

        return {
            "working_time": str(timedelta(seconds=working_seconds)),
            "output_time": str(output_time),
            "day": f"{work_hours}:{work_minutes}",
            "now": str(now),
            "percent": round((working_seconds * 100) / min_daily_working_seconds),
            "balance": str(balance),
            "output_time_with_balance": str(output_time - balance),
            "status": "working" if last_direction == 1 else "taking a break",
            "direction": last_direction,
        }

    def push(self):

        direction = int(self.get_output_time()['direction'])
        push_url = self.base_url + "/api/punches/"

        if direction == 2:
            new_direction = 1
        elif direction == 1:
            new_direction = 2

        push_payload = {
            "direction": new_direction,
            "idEmployee": self.user_id,
            "isReliable": True,
            "timeZone": "Africa/Ceuta"
        }
        response = requests.post(push_url, json=push_payload, headers=self.headers)

        if response.status_code == 200 and response.json().get('result') == True:
            return True

        return False
