import os
import json


class HarAnalyzer:
    __json_dict = {}
    __har_entry_dict = {}
    __video_size_dict = {}
    __dir = None

    def __init__(self, dir, ending):
        file_names = sorted(
            [
                pos_json for pos_json in os.listdir(dir) if
                pos_json.endswith(ending)
            ]
        )

        for file_name in file_names:
            # save the file content as json to our dict
            with open(dir + "/" + file_name, 'r') as myfile:
                data = myfile.read()
                content = json.loads(data)
            self.__json_dict[file_name] = content

            # parse the log entries
            for entry in content["log"]["entries"]:
                har_entry = HarEntry()
                har_entry.url = entry["request"]["url"]
                har_entry.body_size = int(entry["response"]["bodySize"])

                # check if url ends like the CDN's of netflix
                if "video.net/range/" in har_entry.url:
                    har_entry.is_video = True

                    # cut of url at /range to parse it
                    range_url = har_entry.url[(har_entry.url.rindex("/range") + len("/range") + 1):]

                    # remove query parameters
                    if "?" in range_url:
                        range_url = range_url[:range_url.index("?")]

                    # parse range (of the form 7123-8723)
                    ranges = range_url.split("-")
                    har_entry.range_start = int(ranges[0])
                    har_entry.range_end = int(ranges[1])

                self.__har_entry_dict[file_name] = har_entry

            # count file size
            file_size = 0
            for video_id in self.__har_entry_dict:
                entry = self.__har_entry_dict[video_id]
                if entry.is_video:
                    file_size += entry.body_size

            self.__video_size_dict[file_name] = file_size

    def get_har_entry_dict(self):
        """
        get filename => HarEntry dict
        :return:
        """
        return self.__har_entry_dict

    def get_video_size_dict(self):
        """
        get filename => int dict
        :return:
        """
        return self.__video_size_dict


class HarEntry:
    '''
    {
        "pageref": "Page 0",
        "startedDateTime": "2018-04-15T14:38:42.662+02:00",
        "request": {
          "method": "GET",
          "url": "https://ipv4-c006-zrh001-ix.1.oca.nflxvideo.net/range/0-45492?o=RANDOM&v=3&e=1523839122&t=RANDOM",
          "httpVersion": "HTTP/1.1",
          "cookies": [],
          "headers": [],
          "queryString": [
            {
              "name": "o",
              "value": "AQGRWfDjPPk9MDBZQzH58NxUtSksb0m-K3FM_vOtnC6XyPSU5z6WqIciSYI5oLbN5YreaUvVh6e7VA-woU6ucfNcHIQpdMIsOBQcjKl-CXAVYZKgmgZE8Uptv0xc8dUCIu6U_0Y2hoQOJ6xNka-zyvhY8izIf0F970x40oYkOJLoakEhtzgNwIwxAAVfOfKXP3p5WMeiXQ"
            },
            {
              "name": "v",
              "value": "3"
            },
            {
              "name": "e",
              "value": "1523839122"
            },
            {
              "name": "t",
              "value": "FQzIje6TxN9ArzmZ-VjxqVzYM3k"
            }
          ],
          "headersSize": 639,
          "bodySize": 0,
          "comment": ""
        },
        "response": {
          "status": 200,
          "statusText": "OK",
          "httpVersion": "HTTP/1.1",
          "cookies": [],
          "headers": [],
          "content": {
            "size": 0,
            "mimeType": "application/octet-stream",
            "comment": ""
          },
          "redirectURL": "",
          "headersSize": 542,
          "bodySize": 45493,
          "comment": ""
        },
        "cache": {},
        "timings": {
          "comment": "",
          "receive": 134,
          "dns": 3,
          "connect": 82,
          "blocked": 0,
          "send": 0,
          "wait": 4,
          "ssl": 77
        },
        "serverIPAddress": "45.57.19.132",
        "comment": "",
        "time": 225
    }
    '''

    def __init__(self):
        self.url = None
        self.body_size = None
        self.is_video = False
        self.range_start = None
        self.range_end = None

    def get_length(self):
        return self.range_end - self.range_start
