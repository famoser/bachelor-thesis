import matplotlib.pyplot as plt
import sqlite3
from intervaltree import IntervalTree, Interval

from python_libs.config import StaticConfig, Inventory

config = StaticConfig()
inventory = Inventory()

START_AGGREGATION = 1
LAST_AGGREGATION = 10

EPSILON_STEP = 0.1
EPSILON_MAX = 0.6

MAX_PACKAGES_PER_BITRATE = 100

MAX_MOVIES = 5


# int container because can't override attribute
class IntervalNode:
    movie_ids = []

    def __str__(self):
        return str(self.movie_ids)


# get sqlite connection
db_file_name = config.captures_dir + "/data.sqlite"
connection = sqlite3.connect(db_file_name)
cursor = connection.cursor()

for aggregation in range(START_AGGREGATION, LAST_AGGREGATION + 1):
    epsilon = 0

    while epsilon < EPSILON_MAX:
        print("building tree for aggregation " + str(aggregation) + " & epsilon " + str(epsilon))

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
            print("inserting " + str(movie_id) + " (" + str(movie_counter) + "/" + str(len(db_movies)) + ")")
            movie_counter += 1

            if movie_counter > MAX_MOVIES:
                break

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
                        body_sizes_dict[start] = set()
                    body_sizes_dict[start].add(movie_id)
                else:
                    res = body_sizes_tree.search(3, 5, strict=True)
                    elem = None
                    if len(res) == 0:
                        elem = Interval(start, end, IntervalNode())
                        body_sizes_tree.add(elem)
                    else:
                        for entry in res:
                            elem = entry.data

                    elem.data.movie_ids.append(movie_id)

        print("checking for collisions by simulating a capture")

        # prepare collision dict
        collisions = {}
        checked = 0

        movie_counter = 1
        for db_movie in db_movies:
            movie_id = db_movie[0]
            print("simulating for " + str(movie_id) + " (" + str(movie_counter) + "/" + str(len(db_movies)) + ")")
            movie_counter += 1

            if movie_counter > MAX_MOVIES:
                break

            lookup_set = set()
            cursor.execute("SELECT bitrate, id FROM captures WHERE movie_id = ? ORDER BY bitrate", [movie_id])
            db_bitrates = cursor.fetchall()

            for db_bitrate in db_bitrates:
                bitrate = db_bitrate[0]
                capture_id = db_bitrate[1]

                print("accumulating " + str(bitrate))

                # get all video package sizes ordered by capture time
                cursor.execute("SELECT p.body_size "
                               "FROM packets p "
                               "WHERE p.capture_id = ? AND p.body_size > 0 AND aggregation = 1 "
                               "ORDER BY p.id",
                               [capture_id])

                db_packets = cursor.fetchall()

                # aggregate packages for this bitrate
                current_aggregation = 0
                current_value = 0
                total_packets = 0
                for db_packet in db_packets:
                    current_value += db_packet[0]
                    current_aggregation += 1
                    total_packets += 1
                    if total_packets > MAX_PACKAGES_PER_BITRATE:
                        break
                    if current_aggregation == aggregation:
                        lookup_set.add(current_value)
                        current_aggregation = 0
                        current_value = 0

            results = []
            for entry in lookup_set:
                start = (1 - epsilon) * entry
                end = (1 + epsilon) * entry

                if start == end:
                    if start in body_sizes_dict:
                        results.append(body_sizes_dict[start])
                    else:
                        results.append(set())
                else:
                    res = body_sizes_tree.search(start, end)
                    temp_results = set()
                    for re in res:
                        temp_results |= re.data.movie_ids
                    results.append(temp_results)

            possible_movies = set.intersection(*results)
            assert movie_id in possible_movies

            collision_count = len(possible_movies)
            if collision_count not in collisions:
                collisions[collision_count] = 0

            collisions[collision_count] += 1
            checked += 1

        # use percentage & correct order in graph
        figure_collisions = {}
        for i in range(2, max(collisions.keys()) + 1):
            if i in collisions:
                figure_collisions[i] = collisions[i] / checked * 100
            else:
                figure_collisions[i] = 0

        # prepare plot
        fig = plt.figure(figsize=(10, 10))
        plt.xlabel("equal packet sizes over different movies")
        plt.ylabel("packet collision percentage")
        plt.plot(figure_collisions.keys(), figure_collisions.values(), label=str(aggregation), marker='.', linewidth=1)

        # save
        plt.savefig(config.plot_dir + "/collisions_" + str(aggregation) + "_" + str(epsilon) + "_" + str(MAX_PACKAGES_PER_BITRATE) + ".png", dpi=300)
        plt.close()
        print("generated plot")
        print()
        print()

        epsilon += EPSILON_STEP
