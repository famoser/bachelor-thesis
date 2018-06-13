import matplotlib.pyplot as plt
import hashlib
import sqlite3
import json

from python_libs.config import StaticConfig, Inventory

config = StaticConfig()
inventory = Inventory()

START_AGGREGATION = 1
LAST_AGGREGATION = 10

# get sqlite connection
db_file_name = config.captures_dir + "/data.sqlite"
connection = sqlite3.connect(db_file_name)
cursor = connection.cursor()

for aggregation in range(START_AGGREGATION, LAST_AGGREGATION + 1):
    print("starting for aggregation " + str(aggregation))

    cursor.execute("SELECT DISTINCT movie_id FROM captures")
    db_movies = cursor.fetchall()
    total_body_sizes = {}
    movie_counter = 1
    for db_movie in db_movies:
        movie_id = db_movie[0]
        print("checking " + str(movie_id) + " (" + str(movie_counter) + "/" + str(len(db_movies)) + ")")
        movie_counter += 1

        body_sizes = set()
        cursor.execute("SELECT bitrate, id FROM captures WHERE movie_id = ? ORDER BY bitrate", [movie_id])
        db_bitrates = cursor.fetchall()

        for db_bitrate in db_bitrates:
            bitrate = db_bitrate[0]
            capture_id = db_bitrate[1]

            print("accumulating " + str(bitrate))

            # get all video package sizes
            cursor.execute("SELECT p.body_size "
                           "FROM packets p "
                           "WHERE p.capture_id = ? AND p.body_size > 0 AND aggregation = ? "
                           "ORDER BY p.body_size",
                           [capture_id, aggregation])

            db_packets = cursor.fetchall()

            # create packet ranges
            for db_packet in db_packets:
                body_sizes.add(db_packet[0])

        # aggregate
        for body_size in body_sizes:
            if body_size not in total_body_sizes:
                total_body_sizes[body_size] = 0
            total_body_sizes[body_size] += 1

    # get max collision count
    max_collision = 1
    for body_size in total_body_sizes:
        coll_count = total_body_sizes[body_size]
        if max_collision < coll_count:
            max_collision = coll_count

    # prepare collision dict
    collisions = {}
    for count in range(1, max_collision + 1):
        collisions[count] = 0

    # sum up collisions
    for body_size in total_body_sizes:
        collisions[total_body_sizes[body_size]] += 1

    # remove 1 entry
    collisions.pop(1)

    # prepare plot
    fig = plt.figure(figsize=(10, 10))
    plt.xlabel("packet collisions over movies")
    plt.ylabel("collision size")
    plt.plot(collisions.keys(), collisions.values(), label=str(aggregation), marker='.', linewidth=0)

    # save
    plt.savefig(config.plot_dir + "/collisions_" + str(aggregation) + ".png", dpi=300)
    plt.close()
    print("generated plot")
    print()
    print()
