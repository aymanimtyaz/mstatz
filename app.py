import json
import datetime
from urllib.parse import parse_qs


from flask import Flask
from flask import request
from flask import jsonify


app = Flask(__name__)

data1 = json.loads((open('sample_json_1.json', 'r').read()))
data2 = json.loads((open('sample_json_2.json', 'r').read()))
data3 = json.loads((open('sample_json_3.json', 'r').read()))

qs_time_format = "%Y-%m-%dT%H:%M:%SZ"
json_time_format = "%Y-%m-%d %H:%M:%S"

def transform_and_verify_inputs(start_time, end_time, data):

    ''' Transforms start_time and end_time from the query string to python datetimes.
        And verifies of they follow the appropriate format.
    '''

    #       start_time and end_time must be in the following format: '%Y-%m-%dT%H:%M:%SZ'
    try:
        start = datetime.datetime.strptime(start_time, qs_time_format)
        end = datetime.datetime.strptime(end_time, qs_time_format)
    except:
        return {
            "status":"400 BAD METHOD",
            "message":"Please send valid datetimes for start_time and end_time.",
            "example_query_string":"?start_time=2021-01-28T07:30:00Z&end_time=2021-01-28T13:30:00Z"
        }, 400

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

    #       The inputs are valid, second element in the returned tuple is a zero
    return {
        "start":start,
        "end":end
    }, 0

def get_range(start, end, data):

    ''' Get index range for the given start and end time and dataset.
    '''

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

    return start_ind, end_ind

def get_inputs_from_query_string():

    ''' Parse query string to get start_time and end_time.
    '''

    try:
        query_params = parse_qs(request.query_string.decode('utf-8'))
        start_time = query_params.get('start_time')[0]
        end_time = query_params.get('end_time')[0]
    except: 
        #       The query strings must contain both start_time and end_time
        return {
            "status":"400 BAD REQUEST",
            "message":"please send start_time and end_time in the query string."
        }, 400
    #       The query string is valid, second element of the tuple is a zero
    return {
        "start_time":start_time,
        "end_time":end_time
    }, 0
    

@app.route('/question1', methods = ['GET'])
def question1():
    
    i = get_inputs_from_query_string()
    if i[1] != 0:
        return i

    start_time = i[0]['start_time']; end_time = i[0]['end_time']

    v = transform_and_verify_inputs(start_time, end_time, data1)
    if v[1] != 0:
        return v
        
    start = v[0]['start']; end = v[0]['end']
    start_ind, end_ind = get_range(start, end, data1)


    #       start_time      ---> UTC
    #       end_time        ---> UTC
    #       json data1 time ---> UTC
    #       Shift times     ---> IST (UTC + 5:30)

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


    #       Working count of each production line, shift wise

    prod_a_shift_a = 0; prod_a_shift_b = 0; prod_a_shift_c = 0
    prod_b_shift_a = 0; prod_b_shift_b = 0; prod_b_shift_c = 0

    for row in data1[start_ind:end_ind + 1]:
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


@app.route('/question2', methods = ['GET'])
def question2():

    i = get_inputs_from_query_string()
    if i[1] != 0:
        return i

    start_time = i[0]['start_time']; end_time = i[0]['end_time']

    v = transform_and_verify_inputs(start_time, end_time, data2)
    if v[1] != 0:
        return v
        
    start = v[0]['start']; end = v[0]['end']
    start_ind, end_ind = get_range(start, end, data2)

    total_runtime = 0; total_downtime = 0

    for row in data2[start_ind:end_ind+1]:
        runtime = row['runtime']
        downtime = row['downtime']
        if runtime > 1021:
            downtime += (runtime - 1021)
            runtime = 1021
        total_runtime += runtime
        total_downtime += downtime

    def to_format(seconds):

        ''' Returns a string in the required in the output json '''
        
        h = str(seconds//3600)
        remaining_minutes_seconds = seconds%3600
        m = str(remaining_minutes_seconds//60)
        if len(m) < 2:
            m = '0'+m
        s = str(remaining_minutes_seconds%60)
        if len(s) < 2:
            s = '0'+s
        return f"{h}h:{m}m:{s}s"
    
    utilisation = (total_runtime/(total_runtime+total_downtime)) * 100
    return {
        "runtime":to_format(total_runtime),
        "downtime":to_format(total_downtime),
        "utilisation":round(utilisation, 2)
    }, 200

@app.route('/question3', methods = ['GET'])
def question3():
    i = get_inputs_from_query_string()
    if i[1] != 0:
        return i

    start_time = i[0]['start_time']; end_time = i[0]['end_time']

    v = transform_and_verify_inputs(start_time, end_time, data3)
    if v[1] != 0:
        return v
        
    start = v[0]['start']; end = v[0]['end']
    start_ind, end_ind = get_range(start, end, data3)

    belt_data = {}
    for row in data3[start_ind:end_ind + 1]:
        state = row['state']
        belt_1 = int(row['belt1'])
        belt_2 = int(row['belt2'])
        _id = int(row['id'][2:])

        if _id not in belt_data:
            belt_data[_id] = {'count': 0, 'belt_1_total': 0, 'belt_2_total': 0}

        if state == True:
            belt_1 = 0
        else:
            belt_2 = 0
        belt_data[_id]['count'] += 1
        belt_data[_id]['belt_1_total'] += belt_1
        belt_data[_id]['belt_2_total'] += belt_2
    
    belt_data_avg = [{
        "id":key,
        "avg_belt1":belt_data[key]['belt_1_total']//belt_data[key]['count'],
        "avg_belt2":belt_data[key]['belt_2_total']//belt_data[key]['count']
    } for key in belt_data.keys()]

    #       Sorting the list w.r.t. the id.
    belt_data_avg_sorted = sorted(belt_data_avg, key = lambda row: row['id'])

    return jsonify(belt_data_avg_sorted)

if __name__ == '__main__':
    app.run(debug = True)