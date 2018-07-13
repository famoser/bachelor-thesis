# this first queries the expected packets to be captured by an attacker looking at all different bitrates
# then it queries the database with distored package sizes and checking for the amount of matches


import matplotlib.pyplot as plt
import sqlite3

from python_libs.config import StaticConfig, Inventory
from query_helper import QueryHelper

config = StaticConfig()
inventory = Inventory()

START_AGGREGATION = 1
LAST_AGGREGATION = 1

START_PACKAGE_PER_BITRATE = 3
LAST_PACKAGE_PER_BITRATE = 3

EPSILON_STEP = 0.0003
LAST_EPSILON = 0.006

PACKAGE_PER_BITRATE = 3

MAX_MOVIES = 100

# possible modes are bitrate or naive
MODE = "bitrate"

# get sqlite connection
db_file_name = "plot_data.sqlite"
connection = sqlite3.connect(db_file_name)
cursor = connection.cursor()
query_helper = QueryHelper(cursor)

total_package_per_bitrate_plot = {}
for package_per_bitrate in range(START_PACKAGE_PER_BITRATE, LAST_PACKAGE_PER_BITRATE + 1):

    total_plot = {}
    for aggregation in range(START_AGGREGATION, LAST_AGGREGATION + 1):
        packet_table_name = "packets_" + str(aggregation) + "_continuous"

        current_epsilon_multiplication = 0
        epsilon = current_epsilon_multiplication * EPSILON_STEP

        epsilon_collisions = {}

        while epsilon <= LAST_EPSILON:
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
                      " for (package_per_bitrate=" + str(package_per_bitrate) + ", aggregation=" + str(aggregation) + ", epsilon=" + str(epsilon) + ")")

                # get bitrates
                cursor.execute("SELECT id FROM captures WHERE movie_id = ?", [movie_id])
                db_bitrates = cursor.fetchall()

                matching_movies = False
                if MODE == "bitrate":
                    matching_movies = query_helper.bitrate_attack(db_bitrates, db_movies, aggregation, epsilon, packet_table_name, package_per_bitrate)
                elif MODE == "naive":
                    matching_movies = query_helper.naive_attack(db_bitrates, db_bitrates[0][0], db_movies, aggregation, epsilon,
                                                                  packet_table_name, package_per_bitrate)

                if matching_movies is False:
                    print("skipping " + str(movie_id))

                # sanity check
                assert movie_id in matching_movies

                # count collisions
                result_count = len(matching_movies)
                if result_count not in collisions:
                    collisions[result_count] = 0
                collisions[result_count] += 1

                # log collisions to console for fast feedback
                conflict_movies = filter(lambda e: e != movie_id, matching_movies)
                if result_count > 1:
                    print(
                        "collision found for " + str(movie_id) + " with " + ', '.join(str(x) for x in conflict_movies))
                else:
                    print("no collisions found for " + str(movie_id))

            # use percentage & correct order in graph
            if len(collisions) == 0:
                break

            movies_checked = sum(collisions.values())
            figure_collisions = {}
            for i in range(1, max(collisions.keys()) + 1):
                if i in collisions:
                    figure_collisions[i] = collisions[i]
                else:
                    figure_collisions[i] = 0

            # prepare plot
            plt.figure(figsize=(10, 10))
            plt.xlabel("amount of different movies matching fingerprint for " + str(
                movies_checked) + " checked movies with " + str(package_per_bitrate) + " packages per bitrate")
            plt.ylabel("how often this happened")
            plt.plot(figure_collisions.keys(), figure_collisions.values(), label=str(aggregation), marker='.',
                     linewidth=1)

            # save
            plt.savefig(config.plot_dir + "/" + MODE + "_collisions_over_bitrates_" +
                        str(aggregation) + "_" +
                        str(epsilon) + "_" +
                        str(package_per_bitrate) + ".png",
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
            epsilon_collisions[epsilon] = total_collisions / movies_checked * 100

            # prepare next iteration
            current_epsilon_multiplication += 1
            epsilon = current_epsilon_multiplication * EPSILON_STEP

        # prepare plot
        plt.figure(figsize=(10, 10))
        plt.xlabel("epsilon value used")
        plt.ylabel("percentage of movies with fingerprint collisions")
        plt.plot(epsilon_collisions.keys(), epsilon_collisions.values(), label=str(aggregation), marker='.',
                 linewidth=1)

        # save
        plt.savefig(config.plot_dir + "/" + MODE + "_collisions_over_bitrates_over_epsilons_" +
                    str(aggregation) + "_" +
                    str(package_per_bitrate) + ".png",
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
    plt.ylabel("percentage of movies with fingerprint collisions")
    for aggregation in total_plot.keys():
        plt.plot(total_plot[aggregation][0], total_plot[aggregation][1], label=str(aggregation), marker='.',
                 linewidth=1)

    # save
    plt.legend()
    plt.savefig(
        config.plot_dir + "/" + MODE + "_collisions_over_bitrates_over_epsilons_over_aggregations_" + str(
            package_per_bitrate) + ".png",
        dpi=300)
    plt.close()
    print("generated plot")

    for aggregation in total_plot.keys():
        if aggregation not in total_package_per_bitrate_plot:
            total_package_per_bitrate_plot[aggregation] = {}
        total_package_per_bitrate_plot[aggregation][package_per_bitrate] = total_plot[aggregation]


print("generating package bitrate plots")

# plot influence of package per bitrate
for aggregation in total_package_per_bitrate_plot.keys():
    # prepare overall plot
    plt.figure(figsize=(10, 10))
    plt.xlabel("epsilon value used")
    plt.ylabel("percentage of movies with fingerprint collisions")
    for package_per_bitrate in total_package_per_bitrate_plot[aggregation]:
        plt.plot(total_package_per_bitrate_plot[aggregation][package_per_bitrate][0], total_package_per_bitrate_plot[aggregation][package_per_bitrate][1], label=str(package_per_bitrate), marker='.', linewidth=1)

    # save
    plt.legend()
    plt.savefig(
        config.plot_dir + "/" + MODE + "_collisions_over_bitrates_over_epsilons_over_package_per_bitrate_" + str(
            aggregation
        ) + ".png",
        dpi=300)
    plt.close()
    print("generated plot")
