import time
import sqlite3
import operator

from python_libs.config import StaticConfig
from python_libs.netflix_browser import NetflixBrowser
from python_libs.browser_proxy import BrowserProxy
from python_libs.har_analyzer import HarAnalyzer

AGGREGATE = 10


class Configuration:
    def __init__(self):
        # the amount of searches performed
        #
        # 5 because I feel like it
        self.searches_performed = 5


static_config = StaticConfig()

# define the ids we want to capture
config = Configuration()

db_file_name = static_config.captures_dir + "/data.sqlite"
connection = sqlite3.connect(db_file_name)

print("will tests for the last " + str(config.searches_performed) + " packets and try to find match")

cursor = connection.cursor()
# try to find specific packet, and save its capture id to the result set
cursor.execute("SELECT DISTINCT movie_id FROM captures")
movie_ids = []
for item in cursor.fetchall():
    movie_ids.append(str(item[0]))

print("current in DB are " + str(len(movie_ids)) + " movies. They are " + ", ".join(movie_ids))

# initialize the proxy
with BrowserProxy("attack") as proxy:
    # initialize the browser
    with NetflixBrowser(proxy.get_port()) as browser:

        while True:
            # get active capture & analyze it
            capture = proxy.get_active_capture()
            if len(capture) > 0:
                har_entries = HarAnalyzer.get_har_entries_from_json(capture)

                for aggregation in range(0, AGGREGATE):
                    # check if enough packets for aggregation
                    if len(har_entries) - aggregation < 0:
                        continue

                    # aggregate
                    size = 0
                    current_entry = len(har_entries) - 1
                    aggregations_done = 0
                    while current_entry >= 0 and aggregations_done <= aggregation:
                        if har_entries[current_entry].is_video and har_entries[current_entry].body_size > 0:
                            size += har_entries[current_entry].body_size
                            aggregations_done += 1
                        current_entry -= 1

                    # skip if not successfully aggregated
                    if current_entry == 0 and aggregations_done < aggregation:
                        continue

                    print("checking for packet of size " + str(size) + " for aggregation " + str(aggregation + 1))

                    # look up matches
                    cursor = connection.cursor()
                    cursor.execute("SELECT DISTINCT c.movie_id, c.bitrate "
                                   "FROM packets p "
                                   "INNER JOIN captures c ON p.capture_id = c.id "
                                   "WHERE body_size = ? and aggregation = ?",
                                   [size, aggregation + 1])

                    bitrates_by_movie = {}
                    for item in cursor.fetchall():
                        if item[0] not in bitrates_by_movie:
                            bitrates_by_movie[item[0]] = []
                        bitrates_by_movie[item[0]].append(item[1])

                    if len(bitrates_by_movie) == 1:
                        for movie_id in bitrates_by_movie:
                            bitrate_text = "bitrate"
                            if len(bitrates_by_movie[movie_id]) > 1:
                                bitrate_text += "s"
                            print("\tfound results for one movie: " + str(movie_id) +
                                  " at " + bitrate_text + " " + ", ".join(map(str, bitrates_by_movie[movie_id])))

                    if len(bitrates_by_movie) > 0:
                        print("\tfound results for " + str(len(bitrates_by_movie)) + " movies")
                        for movie_id in bitrates_by_movie:
                            bitrate_text = "bitrate"
                            if len(bitrates_by_movie[movie_id]) > 1:
                                bitrate_text += "s"
                            print("\t\t" + str(movie_id) + " found at " + bitrate_text + " " + ", ".join(
                                map(str, bitrates_by_movie[movie_id])))


                # to avoid too much overhead, reset capture after some time
                if len(har_entries) > config.searches_performed * 20:
                    print("reset capture; the next few results may be imprecise")
                    proxy.start_new_capture()

                # visual break & start over
                print()
                print()
