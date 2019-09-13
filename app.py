from flask import Flask, request, jsonify
from flask_api import status
from visualtime_helper import VisualTimeHelper

app = Flask(__name__)


@app.route('/', methods=['GET'])
def index():
    return jsonify({"massage": "hello"})


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

