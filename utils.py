import datetime
from urllib.parse import parse_qs

from flask import request


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

def transform_and_verify_inputs(start_time, end_time, data):

    ''' Transforms start_time and end_time from the query string to python datetimes.
        And verifies if they follow the appropriate format.
    '''

    json_time_format = "%Y-%m-%d %H:%M:%S"
    qs_time_format = "%Y-%m-%dT%H:%M:%SZ"

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

    json_time_format = "%Y-%m-%d %H:%M:%S"

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