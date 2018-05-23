import matplotlib.pyplot as plt
import hashlib
import sqlite3
import json
import dateutil
import time

from python_libs.config import StaticConfig, Inventory

MIN_RESOLUTION = 1
SKIP_FIRST = 100
MAX_RESOLUTION = 400
MIN_Y = 20

config = StaticConfig()
inventory = Inventory()

normalize_cache = None
normalize_cache_result = None


def get_adapted_time(current_point, normalize_point):
    global normalize_cache_result, normalize_cache

    if normalize_point is not normalize_cache:
        normalize_cache_result = convert_to_integer(normalize_point)
        normalize_cache = normalize_point

    return convert_to_integer(current_point) - normalize_cache_result


def convert_to_integer(date):
    my_date = dateutil.parser.parse(date)
    return int(time.mktime(my_date.timetuple()) * 1000 + my_date.microsecond / 1000)
    # the following works but is ugly
    # return int(my_date.strftime("%s")) * 1000 + int(str(my_date.time()).split(".")[1][:3])


# get sqlite connection
db_file_name = config.captures_dir + "/data.sqlite"
connection = sqlite3.connect(db_file_name)
cursor = connection.cursor()

cursor.execute("SELECT DISTINCT movie_id FROM captures")
db_movies = cursor.fetchall()
for db_movie in db_movies:
    movie_id = db_movie[0]
    print("checking " + str(movie_id))

    cursor.execute("SELECT DISTINCT bitrate FROM captures WHERE movie_id = ? ORDER BY bitrate", [movie_id])
    db_bitrates = cursor.fetchall()

    for db_bitrate in db_bitrates:
        bitrate = db_bitrate[0]
        print("")
        print("")
        print("bitrate: " + str(bitrate))

        # show video package accumulation
        cursor.execute("SELECT p.body_size as size, p.start_date_time as start, p.end_date_time as end "
                       "FROM packets p "
                       "INNER JOIN captures c ON c.id = p.capture_id "
                       "WHERE c.movie_id = ? AND c.bitrate = ? AND p.body_size > 0 AND p.is_video = 1 "
                       "ORDER BY p.start_date_time",
                       [movie_id, bitrate])

        db_packets = cursor.fetchall()

        current_skip = SKIP_FIRST
        full_sum = 0
        start = 0
        normalize_point = 0
        all_values = []
        for db_packet in db_packets:
            current_skip -= 1
            if current_skip > 0:
                continue

            if current_skip == 0:
                normalize_point = db_packet[1]

            full_sum += db_packet[0]

        total_time = get_adapted_time(db_packets[len(db_packets) - 1][2], normalize_point) - start
        target_y = full_sum / total_time

        resolution_error = {}
        minimal_error = float("inf")
        for resolution in range(MIN_RESOLUTION, MAX_RESOLUTION):

            current_skip = SKIP_FIRST
            full_sum = 0
            start = 0
            all_values = []
            current_sum = 0
            current_resolution = resolution
            for db_packet in db_packets:
                current_skip -= 1
                if current_skip > 0:
                    continue

                if current_resolution == resolution:
                    start = get_adapted_time(db_packet[1], normalize_point)

                current_sum += db_packet[0]
                current_resolution -= 1

                if current_resolution == 0:
                    current_resolution = resolution
                    end = get_adapted_time(db_packet[2], normalize_point)

                    if end - start == 0:
                        print("0 size")
                    else:
                        y = current_sum / (end - start)
                        if y > MIN_Y:
                            all_values.append(y)

                    current_sum = 0

            resolution_error[resolution] = 0
            for value in all_values:
                resolution_error[resolution] += pow(value, 2)

            minimal_error_now = ""
            if resolution_error[resolution] < minimal_error:
                minimal_error_now = " (MINIMAL)"
                minimal_error = resolution_error[resolution]

            print("error for " + str(resolution) + ": " + str(resolution_error[resolution]) + minimal_error_now)
