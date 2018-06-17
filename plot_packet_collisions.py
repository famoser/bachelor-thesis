import matplotlib.pyplot as plt
import sqlite3
from intervaltree import IntervalTree, Interval

from python_libs.config import StaticConfig, Inventory

config = StaticConfig()
inventory = Inventory()

START_AGGREGATION = 1
LAST_AGGREGATION = 10

EPSILON_STEP = 0.01
EPSILON_MAX = 0.01


# int container because can't override attribute
class IntContainer:
    private = 0

    def __str__(self):
        return str(self.private)


# get sqlite connection
db_file_name = config.captures_dir + "/data.sqlite"
connection = sqlite3.connect(db_file_name)
cursor = connection.cursor()

for aggregation in range(START_AGGREGATION, LAST_AGGREGATION + 1):
    epsilon = 0

    while epsilon < EPSILON_MAX:
        print("starting for aggregation " + str(aggregation) + " & epsilon " + str(epsilon))

        # get count of all indexes packets
        cursor.execute("SELECT COUNT(*) "
                       "FROM packets p "
                       "WHERE aggregation = ?",
                       [aggregation])
        total_packet_count_db = cursor.fetchall()
        total_packet_count = total_packet_count_db[0][0]

        cursor.execute("SELECT DISTINCT movie_id FROM captures")
        db_movies = cursor.fetchall()
        body_sizes_tree = IntervalTree()
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
                start = (1 - epsilon) * body_size
                end = (1 + epsilon) * body_size

                if start == end:
                    if start not in body_sizes_dict:
                        body_sizes_dict[start] = 0
                    body_sizes_dict[start] += 1
                else:
                    res = body_sizes_tree.search(3, 5, strict=True)
                    elem = None
                    if len(res) == 0:
                        elem = Interval(start, end, IntContainer())
                        body_sizes_tree.add(elem)
                    else:
                        for entry in res:
                            elem = entry.data

                    elem.data.private += 1

        # prepare collision dict
        collisions = {}

        # sum up collisions in tree
        for interval in body_sizes_tree:
            res = body_sizes_tree.search(interval.begin, interval.end)
            collision_count = len(res) - 1
            if collision_count not in collisions:
                collisions[collision_count] = 0
            collisions[collision_count] += 1

        # sum up collisions in dictionary
        for entry in body_sizes_dict:
            collision_count = body_sizes_dict[entry]
            if collision_count not in collisions:
                collisions[collision_count] = 0
            collisions[collision_count] += 1

        # use percentage & correct order in graph
        figure_collisions = {}
        for i in range(2, max(collisions.keys())):
            if i in collisions:
                figure_collisions[i] = collisions[i] / total_packet_count * 100
            else:
                figure_collisions[i] = 0

        # prepare plot
        fig = plt.figure(figsize=(10, 10))
        plt.xlabel("equal packet sizes over different movies")
        plt.ylabel("packet collision percentage")
        plt.plot(collisions.keys(), collisions.values(), label=str(aggregation), marker='.', linewidth=1)

        # save
        plt.savefig(config.plot_dir + "/collisions_" + str(aggregation) + "_" + str(epsilon) + ".png", dpi=300)
        plt.close()
        print("generated plot")
        print()
        print()

        epsilon += EPSILON_STEP
