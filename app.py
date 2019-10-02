from flask import Flask, request, jsonify
from flask_api import status

from utils import get_or_create
from visualtime_helper import VisualTimeHelper
import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models import User, Base
from config import DATABASE_URL, USER_TABLE_NAME

app = Flask(__name__)


@app.route('/', methods=['POST'])
def on_event():

    """Handles an event from Hangouts Chat."""

    engine = create_engine(DATABASE_URL)
    if not engine.dialect.has_table(engine, USER_TABLE_NAME):
        Base.metadata.create_all(engine)

    Base.metadata.bind = engine
    DBSession = sessionmaker(bind=engine)
    session = DBSession()

    event = request.get_json()
    email = event['message']['sender']['email']

    if event['type'] == 'ADDED_TO_SPACE' and event['space']['type'] == 'ROOM':
        text = 'Thanks for adding me to "{0}"!'.format(event['space']['displayName'])


    elif event['type'] == 'MESSAGE':
        message = event['message']['text']


        if message.startswith('/login'):
            if len(message.split()) == 2:
                password = message.split()[1]
                user = get_or_create(session, User, email=email, password=password)

        if message.startswith('/info'):
            user = User.query().filter(User.email == email).first()

            visualtime_client = VisualTimeHelper(user.email, user.password)
            visualtime_client.login()

            output_time = visualtime_client.get_output_time()['output_time']
            text = '{0} said: {1}'.format(email, output_time)


    else:
        return
  
    return jsonify({'text': text})



@app.route('/api/getWorkingTime', methods=['POST'])
def get_working_time():
    content = request.get_json(silent=True)
    username = content.get('username')
    password = content.get('password')

    work_hours = content.get('work_hours')
    work_minutes = content.get('work_minutes')

    if work_hours and work_minutes:
        try:
            work_hours = int(work_hours)
            work_minutes = int(work_minutes)
        except:
            errors = {
                "work_hours": "work hours must be integer value",
                "work_minutes": "work minutes must be integer value"
            }
            return errors, status.HTTP_400_BAD_REQUEST

    if not username or not password:
        errors = {"username": "Username is requiered", "password": "Password is requiered"}
        return errors, status.HTTP_400_BAD_REQUEST

    visualtime_client = VisualTimeHelper(username, password)
    visualtime_client.login()

    return jsonify(visualtime_client.get_output_time(work_hours, work_minutes))


if __name__ == '__main__':
    app.run()

