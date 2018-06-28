import urllib
import urllib2
import json

url = 'http://localhost:8000'

data = {
    "nameShifts" : ["MOR", "NON", "NOC"],
    "nameTasks": ['Cook','Bartender', 'Driver'],
    "allWorkers": [
                        {'ID':'001','Name': '---', 'ATasks': [0, 1, 2], 'AShifts': [0, 1, 2]},
                        {'ID':'002','Name': 'OpP', 'ATasks': [0], 'AShifts': [0, 1]},
                        {'ID':'003','Name': 'Op2', 'ATasks': [0], 'AShifts': [0, 1]},
                        {'ID':'004','Name': 'Op3', 'ATasks': [0], 'AShifts': [0, 1, 2]},
                        {'ID':'005','Name': 'Op4', 'ATasks': [0, 2], 'AShifts': [0, 1, 2]},

                        {'ID':'006','Name': 'Op5', 'ATasks': [0], 'AShifts': [0, 1]},
                        {'ID':'007','Name': 'Re1', 'ATasks': [0, 2], 'AShifts': [0, 2]},
                        {'ID':'008','Name': 'Su1', 'ATasks': [1], 'AShifts': [0, 1, 2]},
                        {'ID':'009','Name': 'Su2', 'ATasks': [1], 'AShifts': [0, 1, 2]},
                        {'ID':'010','Name': 'Su3', 'ATasks': [1, 2], 'AShifts': [0, 2]}],
    "allRequirements": [([2, 1, 1], [1, 1, 1], [0, 0, 1]),
                                ([1, 1, 0], [1, 1, 0], [0, 0, 0]),
                                ([2, 1, 0], [1, 1, 0], [0, 0, 0]),
                                ([2, 1, 0], [1, 1, 0], [0, 0, 1]),
                                ([2, 1, 0], [1, 1, 0], [0, 0, 0]),
                                ([3, 1, 1], [1, 1, 0], [0, 0, 1]),
                                ([2, 1, 1], [1, 1, 0], [0, 1, 1])],
    "avoidOvertime": True,
    "maxConsecutiveWorkingDays": 7,
    #Leave requests have the format: [workerId, Day, Shift]
    "leaveRequests": [[2, 0, 0], [1, 1, 1]]  
    # "leaveRequests": []
}

jsonData = json.dumps(data)

print(jsonData)
post_req = urllib2.Request(url)
post_req.add_header('Content-Type', 'application/json')
response = urllib2.urlopen(post_req, json.dumps(data))


print(response.read())
response.close()