import time
import sqlite3
import operator

from python_libs.config import StaticConfig
from python_libs.netflix_browser import NetflixBrowser
from python_libs.browser_proxy import BrowserProxy
from python_libs.har_analyzer import HarAnalyzer


class Configuration:
    def __init__(self):
        # the amount of packets needed before giving a result
        #
        # 5 because I feel like it
        self.packet_threshold = 5

        # how long the process sleeps before trying again
        #
        # choosing 5 before packet length is about 6 seconds
        self.sleep_before_retry = 5


static_config = StaticConfig()

# define the ids we want to capture
config = Configuration()

db_file_name = static_config.captures_dir + "/data.sqlite"
connection = sqlite3.connect(db_file_name)

# test settings
if True:
    config.packet_threshold = 15

print("will tests for the last " + str(config.packet_threshold) + " packets and try to find match")

cursor = connection.cursor()
# try to find specific packet, and save its capture id to the result set
cursor.execute("SELECT DISTINCT movie_id FROM captures")
movie_ids = []
for item in cursor.fetchall():
    if len(movie_ids) > 10:
        break
    movie_ids.append(str(item[0]))

print("current in DB are " + str(len(movie_ids)) + " movies. The first 10 are " + ", ".join(movie_ids))

# initialize the proxy
with BrowserProxy("attack") as proxy:
    # initialize the browser
    with NetflixBrowser(proxy.get_port()) as browser:

        while True:
            # get active capture & analyze it
            capture = proxy.get_active_capture()
            if len(capture) > 0:
                har_entries = HarAnalyzer.get_har_entries_from_json(capture)

                # get info for all relevant packets
                result = {}
                total_packets_found = 0
                same_packets_different_bitrate = 0

                cursor = connection.cursor()
                i = len(har_entries) - 1
                stop_i = len(har_entries) - config.packet_threshold - 1
                while i > stop_i and i > 0:
                    # try to find specific packet, and save its capture id to the result set
                    cursor.execute("SELECT DISTINCT c.movie_id, c.bitrate "
                                   "FROM packets p "
                                   "INNER JOIN captures c ON p.capture_id = c.id "
                                   "WHERE body_size = ? AND is_video = ?",
                                   [har_entries[i].body_size, 1])

                    # add all results to set
                    once = False
                    twice = False
                    for item in cursor.fetchall():
                        result.setdefault(item[0], {})
                        result[item[0]].setdefault(item[1], 0)
                        result[item[0]][item[1]] += 1
                        total_packets_found += 1

                        if once and not twice:
                            same_packets_different_bitrate += 1
                            twice = True
                        once = True

                    # if no video was found
                    if not once:
                        stop_i -= 1

                    i -= 1

                for video_id in result:
                    total_percentage = sum(result[video_id].values()) / \
                                       max(config.packet_threshold, total_packets_found) * 100

                    print_out = str(total_percentage) + "% security: " + str(video_id) + " at "

                    first_time = True
                    for bitrate in result[video_id]:
                        if first_time:
                            first_time = False
                        else:
                            print_out += ", "
                        print_out += str(bitrate) + "k (" + str(result[video_id][bitrate]) + " packets found)"

                    print(print_out)

                if same_packets_different_bitrate:
                    print("in this analysis, " + str(same_packets_different_bitrate) +
                          " packets were found which were identical for multiple bitrates")

                # to avoid too much overhead, reset capture after some time
                if len(har_entries) > config.packet_threshold * 20:
                    print("reset capture; the next few results may be imprecise")
                    proxy.start_new_capture()

            # sleep and try again after some time
            print("waiting for " + str(config.sleep_before_retry) + "s before trying again")
            time.sleep(config.sleep_before_retry)
