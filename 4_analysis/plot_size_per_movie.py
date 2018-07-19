import matplotlib.pyplot as plt
import hashlib
import sqlite3
import json

from python_libs.config import StaticConfig, Inventory

config = StaticConfig()
inventory = Inventory()

# get sqlite connection
db_file_name = "listen_data.sqlite"
connection = sqlite3.connect(db_file_name)
cursor = connection.cursor()

colors = ["blue", "green", "red", "cyan", "magenta", "yellow", "coral", "lime", "orchid"]

cursor.execute("SELECT DISTINCT movie_id FROM captures")
db_movies = cursor.fetchall()
for db_movie in db_movies:
    movie_id = db_movie[0]
    print("checking " + str(movie_id))

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
                points_y.append(packet_sizes[i] / (1024 * 1024))
            axes_bitrate.plot(points_x, points_y,
                              label=str(start_point_of_start_point[packet_sizes_per_start_point_counter]),
                              marker='.', linewidth=0, color=colors[index])

            if len(points_x) > len(before_points_x):
                before_points_x = points_x
                before_points_y = points_y

            packet_sizes_per_start_point_counter += 1

        overall_plot_data[index] = {}
        overall_plot_data[index][0] = before_points_x
        overall_plot_data[index][1] = before_points_y
        overall_plot_data[index][2] = bitrate

        index += 1

    # save
    plt.savefig(config.plot_dir + "/size_per_movie_" + str(movie_id) + ".png", dpi=300)
    plt.close()

    # prepare overall plot
    plt.figure()
    plt.xlabel("packages in correct ordering")
    plt.ylabel("size of packages in megabytes")
    plt.title(str(movie_id) + " - " + inventory.get_name_of(movie_id))
    for index in overall_plot_data.keys():
        plt.plot(overall_plot_data[index][0], overall_plot_data[index][1],
                 label=str(overall_plot_data[index][2]),
                 marker='.', linewidth=0, color=colors[index])

    plt.legend()
    plt.savefig(config.plot_dir + "/size_per_movie_" + str(movie_id) + "_overall.png", dpi=300)
    plt.close()
