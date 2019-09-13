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

        for push in puches:
            if push.get('deleted'):
                continue

            if push.get('direction') == 1:
                input_times.append(datetime.strptime(push.get('dateTime')[0:19], '%Y-%m-%dT%H:%M:%S'))
            elif push.get('direction') == 2:
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
            "output_time_with_balance": str(output_time - balance)
        }