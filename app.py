

import json
from urllib.parse import parse_qs
import datetime

from flask import Flask
from flask import request


app = Flask(__name__)
data = json.loads((open('sample_json_1.json', 'r').read()))

@app.route('/question1', methods = ['GET'])
def question1():
    query_params = parse_qs(request.query_string.decode('utf-8'))
    start_time = query_params.get('start_time')[0]
    end_time = query_params.get('end_time')[0]

    #       start_time     ---> UTC
    #       end_time       ---> UTC
    #       json data time ---> UTC
    #       Shift times    ---> IST (UTC + 5:30)

    qs_time_format = "%Y-%m-%dT%H:%M:%SZ"
    json_time_format = "%Y-%m-%d %H:%M:%S"

    try:
        start = datetime.datetime.strptime(start_time, qs_time_format)
        end = datetime.datetime.strptime(end_time, qs_time_format)
    except:
        return {
            "status":"400 BAD METHOD",
            "message":"Please send valid datetimes for start_time and end_time."
        }



    #       Start time can not be after end time
    if (start > end):
        return {
            "status":"400 BAD REQUEST",
            "message":"Start time can not be after end time."
        }, 400

    #       Start time can not be after the observation range
    if (start > datetime.datetime.strptime(data[-1]['time'], json_time_format)):
        return {
            "status":"400 BAD REQUEST",
            "message":"Start time can not be greater than observation range."
        }, 400

    #       End time can not be before the observation range
    if (end < datetime.datetime.strptime(data[0]['time'], json_time_format)):
        return {
            "status":"400 BAD REQUEST",
            "message":"End time can not be lesser than observation range."
        }, 400

    start_ind = -1
    end_ind = -1

    for idx, row in enumerate(data):
        if datetime.datetime.strptime(row['time'], json_time_format)>= start:
            start_ind = idx
            break
    
    for idx, row in enumerate(data[start_ind:]):
        end_ind = idx + start_ind
        row_datetime = datetime.datetime.strptime(row['time'], json_time_format)
        if row_datetime >= end:
            if row_datetime > end:
                end_ind -= 1
                break
            break


    #       Defining shift timings in UTC time

    #       Shift times in IST
    #       Shift A: 6:00 AM to 2:00 PM
    #       Shift B: 2:00 PM to 8:00 PM
    #       Shift C: 8:00 PM to 6:00 AM

    #       Shift times in UTC (IST - 5:30)
    #       Shift A: 12:30 AM to 8:30 AM
    #       Shift B: 8:30 AM to 2:30 PM
    #       Shift C: 2:30 PM to 12:30 AM

    shift_a_start = datetime.time(hour = 0, minute = 30)
    shift_b_start = datetime.time(hour = 8, minute = 30)
    shift_c_start = datetime.time(hour = 14, minute = 30)

    prod_a_shift_a = 0; prod_a_shift_b = 0; prod_a_shift_c = 0
    prod_b_shift_a = 0; prod_b_shift_b = 0; prod_b_shift_c = 0

    for row in data[start_ind:end_ind+1]:
        row_time = datetime.datetime.strptime(row['time'], json_time_format).time()

        if row['production_A'] == True:
            if row_time <= shift_a_start:        
                prod_a_shift_c += 1
            elif row_time <= shift_b_start:
                prod_a_shift_a += 1
            elif row_time <= shift_c_start:
                prod_a_shift_b += 1
            else:
                prod_a_shift_c += 1

        if row['production_B'] == True:
            if row_time <= shift_a_start:
                prod_b_shift_c += 1
            elif row_time <= shift_b_start:
                prod_b_shift_a += 1
            elif row_time <= shift_c_start:
                prod_b_shift_b += 1
            else:
                prod_b_shift_c += 1

    return {
        "shiftA":{
            "production_A_count":prod_a_shift_a,
            "production_B_count":prod_b_shift_a
        },
        "shiftB":{
            "production_A_count":prod_a_shift_b,
            "production_B_count":prod_b_shift_b
        },
        "shiftC":{
            "production_A_count":prod_a_shift_c,
            "production_B_count":prod_b_shift_c
        }
    }, 200

if __name__ == '__main__':
    app.run(debug = True)