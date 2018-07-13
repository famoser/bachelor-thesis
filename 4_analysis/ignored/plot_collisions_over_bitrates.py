# this first queries the expected packets to be captured by an attacker looking at all different bitrates
# then it queries the database with distored package sizes and checking for the amount of matches


import matplotlib.pyplot as plt
import sqlite3

from python_libs.config import StaticConfig, Inventory

config = StaticConfig()
inventory = Inventory()

START_AGGREGATION = 1
LAST_AGGREGATION = 10

EPSILON_STEP = 0.005
EPSILON_MAX = 0.15

MAX_MOVIES = 100

# get sqlite connection
db_file_name = "plot_data.sqlite"
connection = sqlite3.connect(db_file_name)
cursor = connection.cursor()

total_plot = {}

for aggregation in range(START_AGGREGATION, LAST_AGGREGATION + 1):
    current_epsilon_multiplication = 0
    epsilon = current_epsilon_multiplication * EPSILON_STEP

    epsilon_collisions = {}

    while epsilon < EPSILON_MAX:
        print("building tree for aggregation " + str(aggregation) + " & epsilon " + str(epsilon))

        # prepare collision dict
        collisions = {}
        checked = 0
        check_print_interval = 1000

        # get movies
        cursor.execute("SELECT DISTINCT movie_id FROM captures ORDER BY movie_id")
        db_movies = cursor.fetchall()

        # for each movie; get its packages then query and count the resulting movies
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
            sql = "SELECT body_size, bitrate FROM ("
            middle_sql = ""
            parameters = []
            for db_bitrate in db_bitrates:
                if len(middle_sql) > 0:
                    middle_sql += " UNION "
                middle_sql += "SELECT body_size, bitrate FROM (" \
                              "SELECT DISTINCT c.bitrate as bitrate, p.body_size as body_size, p.id " \
                              "FROM packets_" + str(aggregation) + "_continuous p " \
                                                                   "INNER JOIN captures c ON c.id = p.capture_id " \
                                                                   "WHERE c.id = ? " \
                                                                   "ORDER BY p.id)"
                parameters.append(db_bitrate[0])
            sql += middle_sql + ") ORDER BY bitrate"

            # get available packets
            cursor.execute(sql, parameters)
            db_packets = cursor.fetchall()

            # ensure we have found some packets
            if len(db_packets) == 0:
                continue

            # query matching movies
            sql = ""
            parameters = []
            current_bitrate = 0
            middle_sql = ""
            body_size_sql = ""
            body_size_added = False
            for db_packet in db_packets:
                if current_bitrate != db_packet[1]:
                    current_bitrate = db_packet[1]
                    if len(middle_sql) > 0:
                        middle_sql += " INTERSECT "

                    middle_sql += "SELECT DISTINCT c.movie_id " \
                                  "FROM packets_" + str(aggregation) + "_continuous p " \
                                                                       "INNER JOIN captures c ON c.id = p.capture_id " \
                                                                       "WHERE "

                    body_size_sql = ""
                    body_size_added = False

                if body_size_added:
                    middle_sql += " OR "
                body_size_added = True

                middle_sql += "(p.body_size >= ? AND p.body_size <= ?)"
                parameters.append((1 - epsilon) * db_packet[0])
                parameters.append((1 + epsilon) * db_packet[0])

            sql += middle_sql
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

            # log collisions to console for fast feedback
            conflict_movies = filter(lambda e: e != movie_id, possible_movies)
            if result_count > 1:
                print("collision found for " + str(movie_id) + " with " + ', '.join(str(x) for x in conflict_movies))
            else:
                print("no collisions found for " + str(movie_id))

        # use percentage & correct order in graph
        figure_collisions = {}
        for i in range(1, max(collisions.keys()) + 1):
            if i in collisions:
                figure_collisions[i] = collisions[i]
            else:
                figure_collisions[i] = 0

        # prepare plot
        plt.figure(figsize=(10, 10))
        plt.xlabel("amount of different movies matching fingerprint")
        plt.ylabel("how often this happened")
        assert sum(figure_collisions.values()) == len(db_movies)
        plt.plot(figure_collisions.keys(), figure_collisions.values(), label=str(aggregation), marker='.', linewidth=1)

        # save
        plt.savefig(config.plot_dir + "/collisions_over_bitrates_" +
                    str(aggregation) + "_" +
                    str(epsilon) + ".png",
                    dpi=300)
        plt.close()
        print("generated plot")
        print()
        print()

        # remember collisions for overall plot
        total_collisions = 0
        for i in range(2, max(collisions.keys()) + 1):
            if i in collisions:
                total_collisions += collisions[i]
        epsilon_collisions[epsilon] = total_collisions

        # prepare next iteration
        current_epsilon_multiplication += 1
        epsilon = current_epsilon_multiplication * EPSILON_STEP

    # prepare plot
    plt.figure(figsize=(10, 10))
    plt.xlabel("epsilon value used")
    plt.ylabel("movies with fingerprint collisions")
    plt.plot(epsilon_collisions.keys(), epsilon_collisions.values(), label=str(aggregation), marker='.', linewidth=1)

    # save
    plt.savefig(config.plot_dir + "/collisions_over_bitrates_over_epsilons_" +
                str(aggregation) + ".png",
                dpi=300)
    plt.close()
    print("generated plot")

    total_plot[aggregation] = {}
    total_plot[aggregation][0] = epsilon_collisions.keys()
    total_plot[aggregation][1] = epsilon_collisions.values()
    print()
    print()


# prepare overall plot
plt.figure(figsize=(10, 10))
plt.xlabel("epsilon value used")
plt.ylabel("movies with fingerprint collisions")
for aggregation in total_plot.keys():
    plt.plot(total_plot[0], total_plot[1], label=str(aggregation), marker='.', linewidth=1)

# save
plt.savefig(config.plot_dir + "/collisions_over_bitrates_over_epsilons.png", dpi=300)
plt.close()
print("generated plot")
