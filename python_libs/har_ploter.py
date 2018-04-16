import os
import json


class HarPlotter:
    __file_data = {}
    __dir = None

    def __init__(self, dir, ending):
        file_names = sorted(
            [pos_json for pos_json in os.listdir(dir) if
             pos_json.endswith(ending)]
        )

        file_data = {}
        for file_name in file_names:
            with open(dir + "/" + file_name, 'r') as myfile:
                data = myfile.read()
                content = json.loads(data)
                self.__file_data[file_name] = content


        file_size = 0
        for entry in content["log"]["entries"]:
            url = entry["request"]["url"]
            size = entry["response"]["bodySize"]
            if "video.net/range/" in url:
                file_size += size

        __files = files
