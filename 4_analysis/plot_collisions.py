# plots the size of packet size collision with other movies as the source packet

import matplotlib.pyplot as plt
import sqlite3
from intervaltree import IntervalTree, Interval

from python_libs.config import StaticConfig, Inventory

config = StaticConfig()
inventory = Inventory()

START_AGGREGATION = 1
LAST_AGGREGATION = 10


# int container because can't override attribute
class IntContainer:
    private = 0

    def __str__(self):
        return str(self.private)


# get sqlite connection
db_file_name = "plot_data.sqlite"
connection = sqlite3.connect(db_file_name)
cursor = connection.cursor()

total_plot = {}
for aggregation in range(START_AGGREGATION, LAST_AGGREGATION + 1):
    print("starting for aggregation " + str(aggregation))

    # get count of all indexes packets
    cursor.execute("SELECT COUNT(*) "
                   "FROM packets p "
                   "WHERE aggregation = ?",
                   [aggregation])
    total_packet_count_db = cursor.fetchall()
    total_packet_count = total_packet_count_db[0][0]

    cursor.execute("SELECT DISTINCT movie_id FROM captures")
    db_movies = cursor.fetchall()
    body_sizes_dict = {}

    movie_counter = 1
    for db_movie in db_movies:
        movie_id = db_movie[0]
        print("checking " + str(movie_id) + " (" + str(movie_counter) + "/" + str(len(db_movies)) + ")")
        movie_counter += 1

        movie_body_sizes = set()
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
                movie_body_sizes.add(db_packet[0])

        # aggregate
        for body_size in movie_body_sizes:
            if body_size not in body_sizes_dict:
                body_sizes_dict[body_size] = 0
            body_sizes_dict[body_size] += 1

    # prepare collision dict
    collisions = {}

    # sum up collisions in dictionary
    for entry in body_sizes_dict:
        collision_count = body_sizes_dict[entry]
        if collision_count not in collisions:
            collisions[collision_count] = 0
        collisions[collision_count] += 1

    # use percentage & correct order in graph
    figure_collisions = {}
    for i in range(2, max(collisions.keys()) + 1):
        if i in collisions:
            figure_collisions[i] = collisions[i] / total_packet_count * 100
        else:
            figure_collisions[i] = 0

    # prepare plot
    fig = plt.figure(figsize=(10, 10))
    plt.xlabel("equal packet sizes over different movies")
    plt.ylabel("packet collision percentage")
    plt.plot(figure_collisions.keys(), figure_collisions.values(), label=str(aggregation), marker='.', linewidth=1)

    # save
    plt.savefig(config.plot_dir + "/collisions_" + str(aggregation) + ".png", dpi=300)
    plt.close()

    total_plot[aggregation] = {}
    total_plot[aggregation][0] = figure_collisions.keys()
    total_plot[aggregation][1] = figure_collisions.values()

    print("generated plot")
    print()
    print()

fig = plt.figure(figsize=(10, 10))
plt.xlabel("equal packet sizes over different movies")
plt.ylabel("packet collision percentage")
for aggregation in total_plot.keys():
    plt.plot(total_plot[aggregation][0], total_plot[aggregation][1], label=str(aggregation), marker='.', linewidth=1)
plt.legend()
# save
plt.savefig(config.plot_dir + "/collisions.png", dpi=300)
plt.close()
print("generated plot")
