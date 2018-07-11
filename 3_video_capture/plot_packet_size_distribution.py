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

    cursor.execute("SELECT bitrate, id FROM captures WHERE movie_id = ? ORDER BY bitrate", [movie_id])
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
        capture_id = db_bitrate[1]

        print("accumulating " + str(bitrate))

        if bitrate > 460:
            continue

        axes_bitrate = fig.add_subplot(int(round(len(db_bitrates) / 2, 0) + 1), 3, bitrate_counter)
        bitrate_counter += 1
        if bitrate_counter % 3 == 1:
            bitrate_counter += 1

        # get all video package sizes
        cursor.execute("SELECT p.body_size "
                       "FROM packets p "
                       "WHERE p.capture_id = ? AND p.body_size > 0 AND aggregation = 1 "
                       "ORDER BY p.body_size",
                       [capture_id])

        db_packets = cursor.fetchall()

        # create packet ranges
        body_sizes = {}
        for entry in range(0, db_packets[len(db_packets)-1][0] + 1):
            body_sizes[entry] = 0

        for db_packet in db_packets:
            body_sizes[db_packet[0]] += 1

        # remove 0 values
        body_sizes =  {x:y for x,y in body_sizes.items() if y != 0}

        axes_bitrate.plot(body_sizes.keys(), body_sizes.values(),
                          label=str(bitrate),
                          marker='.', linewidth=0)

    # axes_full.plot(before_points_x, before_points_y, label=str(bitrate), marker='.', linewidth=0)

    # save
    plt.savefig(config.plot_dir + "/capture_bitrate_levels_" + str(movie_id) + ".png", dpi=300)
    plt.close()
