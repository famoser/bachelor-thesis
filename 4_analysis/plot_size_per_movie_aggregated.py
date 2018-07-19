# this script plots aggregated package sizes per movie

import matplotlib.pyplot as plt
import sqlite3
import dateutil
import time

from python_libs.config import StaticConfig, Inventory

START_AGGREGATION = 1
AGGREGATION_STEP = 9
END_AGGREGATION = 29

MIN_Y = 20

SIZE_ADAPT = 1024*1024

config = StaticConfig()
inventory = Inventory()

normalize_cache = None
normalize_cache_result = None

colors = ["blue", "green", "red", "cyan", "magenta", "yellow", "coral", "lime", "orchid"]


def get_adapted_time(current_point, normalize_point):
    global normalize_cache_result, normalize_cache

    if normalize_point is not normalize_cache:
        normalize_cache_result = convert_to_integer(normalize_point)
        normalize_cache = normalize_point

    return (convert_to_integer(current_point) - normalize_cache_result) / (1000*60)


def convert_to_integer(date):
    # returns a minute float of the date
    my_date = dateutil.parser.parse(date)
    return int(time.mktime(my_date.timetuple()) * 1000 + my_date.microsecond / 1000)


# get sqlite connection
db_file_name = "listen_data.sqlite"
connection = sqlite3.connect(db_file_name)
cursor = connection.cursor()

cursor.execute("SELECT DISTINCT movie_id FROM captures")
db_movies = cursor.fetchall()

for db_movie in db_movies:
    movie_id = db_movie[0]
    if movie_id != 70101276:
        continue

    aggregation = START_AGGREGATION
    while aggregation < END_AGGREGATION:
        print("checking " + str(movie_id) + " at " + str(aggregation))

        cursor.execute("SELECT DISTINCT bitrate FROM captures WHERE movie_id = ? ORDER BY bitrate", [movie_id])
        db_bitrates = cursor.fetchall()

        # prepare plots
        fig = plt.figure(figsize=(10, 14))
        plt.axis('off')
        plt.xlabel("packages in correct ordering")
        plt.ylabel("size of packages in megabytes")
        plt.title(str(movie_id) + " - " + inventory.get_name_of(movie_id))

        overall_plot_data = {}
        index = 0
        max_rows = int((len(db_bitrates) + 1) / 2)
        for db_bitrate in db_bitrates:
            bitrate = db_bitrate[0]
            axes_bitrate = fig.add_subplot(max_rows, 2, index + 1)
            axes_bitrate.set_title(str(bitrate))

            # show video package accumulation
            cursor.execute("SELECT p.body_size as size, p.start_date_time as start, p.end_date_time as end "
                           "FROM packets p "
                           "INNER JOIN captures c ON c.id = p.capture_id "
                           "WHERE c.movie_id = ? AND c.bitrate = ? AND p.body_size > 0 AND p.is_video = 1 "
                           "ORDER BY p.id",
                           [movie_id, bitrate])

            db_packets = cursor.fetchall()

            full_sum = 0
            current_sum = 0
            start = 0
            end = 0
            normalize_point = db_packets[0][1]
            for db_packet in db_packets:
                if end - start == aggregation:
                    y = current_sum / SIZE_ADAPT
                    axes_bitrate.plot([start, end], [y, y], marker='.', linewidth=1, color=colors[index])
                    start = end
                    current_sum = 0

                current_sum += db_packet[0]
                end += 1

            index += 1

        # save
        plt.savefig(config.plot_dir + "/size_per_movie_aggregated_" + str(movie_id) + "_" + str(aggregation) + ".png", dpi=300)
        plt.close()

        aggregation += AGGREGATION_STEP
