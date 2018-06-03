# this script sums up the video size per video

import os
import json

from python_libs.config import StaticConfig

config = StaticConfig()


def sizeof_fmt(num, suffix='B'):
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


json_files = [pos_json for pos_json in os.listdir(config.captures_dir) if
              pos_json.endswith('.json')]

json_files = sorted(json_files)

sizePerFile = {}

for json_file in json_files:
    file_path = config.captures_dir + "/" + json_file
    with open(file_path, 'r') as file:
        data = file.read()

    content = json.loads(data)
    totalSize = 0
    for entry in content["log"]["entries"]:
        if "video.net/range/" in entry["request"]["url"]:
            totalSize = totalSize + entry["response"]["bodySize"]

    if totalSize == 0:
        os.remove(file_path)
    sizePerFile[json_file] = totalSize

result = ''
for key in sizePerFile:
    result += key + ': ' + sizeof_fmt(sizePerFile[key]) + '\n'

with open(config.analyze_dir + "/" + 'analyze_result.txt', "w") as text_file:
    print(result, file=text_file)
