# plots the average bandwidth used at specific points in time; else its 0

import matplotlib.pyplot as plt
import sqlite3
import dateutil
import time

from python_libs.config import StaticConfig, Inventory

RESOLUTION = 10

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
db_file_name = "listen_data.sqlite"
connection = sqlite3.connect(db_file_name)
cursor = connection.cursor()

cursor.execute("SELECT DISTINCT movie_id FROM captures")
db_movies = cursor.fetchall()
for db_movie in db_movies:
    movie_id = db_movie[0]
    print("checking " + str(movie_id))

    cursor.execute("SELECT DISTINCT bitrate FROM captures WHERE movie_id = ? ORDER BY bitrate", [movie_id])
    db_bitrates = cursor.fetchall()

    # prepare plots
    fig = plt.figure(figsize=(10, 10))
    axes_full = fig.add_subplot(1, 3, 1)
    plt.xlabel("packets ordered by time")
    plt.ylabel("size of packet over time")
    plt.title(str(movie_id) + " - " + inventory.get_name_of(movie_id))

    bitrate_counter = 2
    for db_bitrate in db_bitrates:
        bitrate = db_bitrate[0]
        axes_bitrate = fig.add_subplot(int(round(len(db_bitrates) / 2, 0) + 1), 3, bitrate_counter)
        axes_bitrate.set_title(str(bitrate))
        axes_bitrate.set_xlabel("time")
        axes_bitrate.set_ylabel("bandwidth used")

        bitrate_counter += 1
        if bitrate_counter % 3 == 1:
            bitrate_counter += 1

        # show video package accumulation
        cursor.execute("SELECT p.body_size as size, p.start_date_time as start, p.end_date_time as end "
                       "FROM packets p "
                       "INNER JOIN captures c ON c.id = p.capture_id "
                       "WHERE c.movie_id = ? AND c.bitrate = ? AND p.body_size > 0 AND p.is_video = 1 "
                       "ORDER BY p.start_date_time",
                       [movie_id, bitrate])

        db_packets = cursor.fetchall()

        sum = 0
        full_sum = 0
        counter = 0
        start = 0
        normalize_point = db_packets[0][1]
        for db_packet in db_packets:
            # create line from x1 to x2, depending on size of packet
            start = get_adapted_time(db_packet[1], normalize_point)
            end = get_adapted_time(db_packet[2], normalize_point)
            if end - start == 0:
                print("0 size")
            else:
                y = db_packet[0] / (end - start)
                axes_bitrate.plot([start, end], [y, y], marker='.', linewidth=1)

            # for full analyis
            counter += 1
            sum += db_packet[0]

        total_time = get_adapted_time(db_packets[len(db_packets) - 1][2], normalize_point)
        y = sum / total_time
        axes_full.plot([0, total_time], [y, y], label=str(bitrate), marker='.', linewidth=1)
        axes_full.legend()

    # save
    plt.savefig(config.plot_dir + "/capture_flow_per_time_" + str(movie_id) + ".png", dpi=300)
    plt.close()
