import os
import json


class HarAnalyzer:
    __file_names = []
    __json_dict = {}
    __har_entries_dict = {}
    __capture_statistics = {}
    __dir = None

    def __init__(self, file_dir, ending):
        # get sorted files
        self.__file_names = sorted(
            [
                pos_json for pos_json in os.listdir(file_dir) if
                pos_json.endswith(ending)
            ]
        )

        # create json dict
        for file_name in self.__file_names:
            # save the file content as json to our dict
            with open(file_dir + "/" + file_name, 'r') as file:
                data = file.read()
                content = json.loads(data)
            self.__json_dict[file_name] = content

        # create har dict
        for file_name in self.__file_names:
            self.__har_entries_dict[file_name] = self.get_har_entries_from_json(self.__json_dict[file_name]["packets"])

            # parse the log entries
            for entry in self.__json_dict[file_name]["packets"]:
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

                self.__har_entries_dict[file_name].append(har_entry)

        # create capture statistics dict
        for file_name in self.__file_names:

            # calculate video size
            video_size = 0
            packet_count = 0
            for entry in self.__har_entries_dict[file_name]:
                if entry.is_video:
                    video_size += entry.body_size
                    packet_count += 1

            # create statistics object
            capture_statistics = CaptureStatistics()
            capture_statistics.video_size = video_size
            capture_statistics.packet_count = packet_count
            if "capture_duration" in self.__json_dict[file_name]["configuration"]:
                capture_statistics.capture_length = self.__json_dict[file_name]["configuration"]["capture_duration"]

            self.__capture_statistics[file_name] = capture_statistics

    @staticmethod
    def get_har_entries_from_json(json):
        res = []

        # parse the log entries
        for entry in json:
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

            res.append(har_entry)

        return res

    def get_json_dict(self):
        """
        get filename => json dict
        :return:
        """
        return self.__json_dict

    def get_har_entries_dict(self):
        """
        get filename => HarEntry[] dict
        :return:
        """
        return self.__har_entries_dict

    def get_file_names(self):
        """
        get list of filenames
        :return:
        """
        return self.__file_names

    def get_capture_statistics(self):
        """
        get filename => CaptureStatistics
        :return:
        """
        return self.__capture_statistics


class HarEntry:
    """
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
    """

    def __init__(self):
        self.url = None
        self.body_size = None
        self.is_video = False
        self.range_start = None
        self.range_end = None

    def __repr__(self):
        return self.__dict__.__repr__()

    def get_length(self):
        return self.range_end - self.range_start


class CaptureStatistics:
    def __init__(self):
        self.video_size = 0
        self.capture_length = 0
        self.packet_count = 0

    def get_throughput(self):
        return self.video_size / self.capture_length

    def get_packet_count(self):
        return self.packet_count
