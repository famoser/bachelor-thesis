import matplotlib.pyplot as plt
import hashlib
import sqlite3
import json

from python_libs.config import StaticConfig, Inventory

config = StaticConfig()
inventory = Inventory()

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

    # prepare plots
    fig = plt.figure(figsize=(10, 10))
    axes_full = fig.add_subplot(1, 3, 1)
    plt.xlabel("packets in correct ordering")
    plt.ylabel("size of packet in bytes")
    plt.title(str(movie_id) + " - " + inventory.get_name_of(movie_id))

    bitrate_counter = 2
    for db_bitrate in db_bitrates:
        bitrate = db_bitrate[0]
        axes_bitrate = fig.add_subplot(int(round(len(db_bitrates) / 2, 0) + 1), 3, bitrate_counter)
        bitrate_counter += 1
        if bitrate_counter % 3 == 1:
            bitrate_counter += 1

        # show video package accumulation
        cursor.execute("SELECT DISTINCT p.range_start as start, p.range_end as end "
                       "FROM packets p "
                       "INNER JOIN captures c ON c.id = p.capture_id "
                       "WHERE c.movie_id = ? AND c.bitrate = ? AND p.body_size > 0 AND p.is_video = 1 "
                       "ORDER BY p.range_start",
                       [movie_id, bitrate])

        db_packets = cursor.fetchall()

        # create packet ranges
        start_points = {}
        packet_sizes_per_start_point = []
        start_point_of_start_point = []
        for db_packet in db_packets:
            found = False

            # extend existing start points
            counter = 0
            for start_point in start_points:
                if start_points[start_point] == db_packet[0]:
                    start_points[start_point] = db_packet[1] + 1
                    packet_sizes_per_start_point[counter].append(db_packet[1] - db_packet[0])
                    found = True
                counter += 1

            # create new start point of not found
            if not found:
                start_points[db_packet[0]] = db_packet[1] + 1
                packet_sizes_per_start_point.append([])
                start_point_of_start_point.append(db_packet[0])

        before_points_x = []
        before_points_y = []
        packet_sizes_per_start_point_counter = 0
        for packet_sizes in packet_sizes_per_start_point:
            points_x = []
            points_y = []
            for i in range(0, len(packet_sizes) - 1):
                points_x.append(i + 1)
                points_y.append(packet_sizes[i])
            axes_bitrate.plot(points_x, points_y,
                              label=str(start_point_of_start_point[packet_sizes_per_start_point_counter]),
                              marker='.', linewidth=0)

            if len(points_x) > len(before_points_x):
                before_points_x = points_x
                before_points_y = points_y

            packet_sizes_per_start_point_counter += 1

        axes_full.plot(before_points_x, before_points_y, label=str(bitrate), marker='.', linewidth=0)

    # save
    plt.savefig(config.plot_dir + "/capture_bitrate_levels_" + str(movie_id) + ".png", dpi=300)
    plt.close()
