import os
import json


def sizeof_fmt(num, suffix='B'):
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


json_files = [pos_json for pos_json in os.listdir(".") if pos_json.endswith('.json')]

sizePerFile = {}

for file in json_files:
    with open(file, 'r') as myfile:
        data = myfile.read()

    content = json.loads(data)
    totalSize = 0
    for entry in content["log"]["entries"]:
        if "video.net/range/" in entry["request"]["url"]:
            totalSize = totalSize + entry["response"]["bodySize"]

    sizePerFile[file] = totalSize

result = ''
for key in sizePerFile:
    result += key + ': ' + sizeof_fmt(sizePerFile[key]) + '\n'

with open('analyze_result.txt', "w") as text_file:
    print(result, file=text_file)
