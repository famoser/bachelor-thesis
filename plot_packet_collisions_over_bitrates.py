import matplotlib.pyplot as plt
import sqlite3
from intervaltree import IntervalTree, Interval

from python_libs.config import StaticConfig, Inventory

config = StaticConfig()
inventory = Inventory()

START_AGGREGATION = 1
LAST_AGGREGATION = 10

EPSILON_STEP = 0.05
EPSILON_MAX = 0.3

MAX_MOVIES = 5

CONTINUOUS = True
MAX_PACKAGES_PER_BITRATE = 50


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

        # prepare collision dict
        collisions = {}
        checked = 0
        check_print_interval = 1000

        # get movies
        cursor.execute("SELECT DISTINCT movie_id FROM captures ORDER BY movie_id")
        db_movies = cursor.fetchall()

        for db_movie in db_movies:
            movie_id = db_movie[0]

            checked += 1
            if checked > MAX_MOVIES:
                continue

            print("checking " + str(checked) + " of " + str(len(db_movies)) +
                  " for (aggregation=" + str(aggregation) + ", epsilon=" + str(epsilon) + ")")

            # get bitrates
            cursor.execute("SELECT id FROM captures WHERE movie_id = ?", [movie_id])
            db_bitrates = cursor.fetchall()

            # create sql to get all packets we "sniffed"
            sql = ""
            parameters = []
            for db_bitrate in db_bitrates:
                if len(sql) > 0:
                    sql += " UNION "
                sql += "SELECT body_size FROM (SELECT DISTINCT p.body_size as body_size, p.id " \
                       "FROM packets p " \
                       "INNER JOIN captures c ON c.id = p.capture_id " \
                       "WHERE p.aggregation = ? AND p.continuous = ? AND c.id = ? " \
                       "ORDER BY p.id " \
                       "LIMIT ?)"
                parameters.append(aggregation)
                parameters.append(CONTINUOUS)
                parameters.append(db_bitrate[0])
                parameters.append(MAX_PACKAGES_PER_BITRATE)

            # get available packets
            cursor.execute(sql, parameters)
            db_packets = cursor.fetchall()

            # query matching movies
            sql = "SELECT DISTINCT c.movie_id " \
                  "FROM packets p " \
                  "INNER JOIN captures c ON p.capture_id = c.id " \
                  "WHERE p.aggregation = ? AND p.continuous = ?"
            parameters = [aggregation, CONTINUOUS]
            middle_sql = ""
            for db_packet in db_packets:
                if len(middle_sql) > 0:
                    middle_sql += " OR "
                middle_sql += "(p.body_size >= ? AND p.body_size <= ?)"
                parameters.append((1 - epsilon) * db_packet[0])
                parameters.append((1 + epsilon) * db_packet[0])

            if len(middle_sql) > 0:
                if middle_sql.endswith("OR "):
                    middle_sql = middle_sql[:-3]
                sql += " AND (" + middle_sql + ")"

            cursor.execute(sql, parameters)
            db_possible_movies = cursor.fetchall()

            # sanity check
            possible_movies = []
            for db_possible_movie in db_possible_movies:
                possible_movies.append(db_possible_movie[0])

            assert movie_id in possible_movies

            # count collisions
            result_count = len(db_possible_movies)
            if result_count not in collisions:
                collisions[result_count] = 0
            collisions[result_count] += 1

        # use percentage & correct order in graph
        figure_collisions = {}
        for i in range(2, max(collisions.keys()) + 1):
            if i in collisions:
                figure_collisions[i] = collisions[i] / checked * 100
            else:
                figure_collisions[i] = 0

        # prepare plot
        fig = plt.figure(figsize=(10, 10))
        plt.xlabel("movies in result set")
        plt.ylabel("packet collision percentage")
        plt.plot(figure_collisions.keys(), figure_collisions.values(), label=str(aggregation), marker='.', linewidth=1)

        # save
        plt.savefig(config.plot_dir + "/collisions_" + str(aggregation) + "_" + str(epsilon) + "_" + str(
            MAX_PACKAGES_PER_BITRATE) + ".png", dpi=300)
        plt.close()
        print("generated plot")
        print()
        print()

        epsilon += EPSILON_STEP
