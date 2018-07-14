# this simulates different attacker modes and generates an abundance of plots
# you can change any values written in CAPS to get the desired plots with the desired resolution
# this script has grown a lot; it would need large refactoring to be really readable again
# to make it easier to understand the attacks we have however externalized that part of the code
# this file does therefore only contain the logic needed for plotting

import matplotlib.pyplot as plt
import sqlite3

from python_libs.config import StaticConfig, Inventory
from query_helper import QueryHelper

config = StaticConfig()
inventory = Inventory()

START_AGGREGATION = 10
LAST_AGGREGATION = 10

START_PACKAGE_PER_BITRATE = 1
LAST_PACKAGE_PER_BITRATE = 1

EPSILON_STEP = 0.001
LAST_EPSILON = 0.04

MAX_MOVIES = 100

# switch modes if you want more plots of the OTHER_MODE mode
MODE = "bitrate"
OTHER_MODE = "naive"

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
        other_epsilon_collisions = {}
        collision_numbers = {}

        while epsilon <= LAST_EPSILON:
            # prepare collision dict
            mode_collisions = {}
            other_collisions = {}
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
                      " for (package_per_bitrate=" + str(package_per_bitrate) + ", aggregation=" + str(
                    aggregation) + ", epsilon=" + str(epsilon) + ")")

                # get bitrates
                cursor.execute("SELECT id FROM captures WHERE movie_id = ?", [movie_id])
                db_bitrates = cursor.fetchall()

                # perform attacks
                bitrate_matching_movies = query_helper.bitrate_attack(db_bitrates, db_movies, aggregation, epsilon,
                                                              packet_table_name, package_per_bitrate)
                naive_matching_movies = query_helper.naive_attack(db_bitrates, db_bitrates[0][0], db_movies,
                                                                  aggregation,
                                                                  epsilon,
                                                                  packet_table_name, package_per_bitrate)
                matching_movies = False
                other_matching_movies = False
                if MODE == "bitrate":
                    matching_movies = bitrate_matching_movies
                    other_matching_movies = naive_matching_movies
                elif MODE == "naive":
                    matching_movies = naive_matching_movies
                    other_matching_movies = bitrate_matching_movies

                if matching_movies is False:
                    print("skipping " + str(movie_id))
                    continue

                # sanity check
                assert movie_id in matching_movies

                # count collisions
                result_count = len(matching_movies)
                if result_count not in mode_collisions:
                    mode_collisions[result_count] = 0
                mode_collisions[result_count] += 1

                # count other collisions
                if other_matching_movies is not False:
                    result_count = len(other_matching_movies)
                    if result_count not in other_collisions:
                        other_collisions[result_count] = 0
                    other_collisions[result_count] += 1

                # log collisions to console for fast feedback
                conflict_movies = filter(lambda e: e != movie_id, matching_movies)
                if result_count > 1:
                    print(
                        "collision found for " + str(movie_id) + " with " + ', '.join(str(x) for x in conflict_movies))
                else:
                    print("no collisions found for " + str(movie_id))

            # use percentage & correct order in graph
            if len(mode_collisions) == 0:
                break

            # create figure collision dict
            movies_checked = sum(mode_collisions.values())
            figure_collisions = {}
            for i in range(1, max(mode_collisions.keys()) + 1):
                if i in mode_collisions:
                    figure_collisions[i] = mode_collisions[i]
                else:
                    figure_collisions[i] = 0

            # prepare plot
            plt.figure(figsize=(10, 10))
            plt.xlabel("amount of different movies matching fingerprint for " +
                       str(movies_checked) + " checked movies with " +
                       str(package_per_bitrate) + " packages per bitrate")
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

            # remember collisions for the aggregated plot
            collision_numbers[epsilon] = {}
            collision_numbers[epsilon][0] = figure_collisions.keys()
            collision_numbers[epsilon][1] = figure_collisions.values()

            # remember collisions for overall plot
            total_collisions = 0
            for i in range(2, max(mode_collisions.keys()) + 1):
                if i in mode_collisions:
                    total_collisions += mode_collisions[i]
            epsilon_collisions[epsilon] = total_collisions / movies_checked * 100

            # remember collisions for secondary plot
            total_collisions = 0
            for i in range(2, max(other_collisions.keys()) + 1):
                if i in other_collisions:
                    total_collisions += other_collisions[i]
            other_epsilon_collisions[epsilon] = total_collisions / movies_checked * 100

            # prepare next iteration
            current_epsilon_multiplication += 1
            epsilon = current_epsilon_multiplication * EPSILON_STEP

        # prepare plot
        plt.figure(figsize=(10, 10))
        plt.xlabel("amount of different movies matching fingerprint")
        plt.ylabel("how often this happened")
        for epsilon in collision_numbers:
            plt.plot(collision_numbers[epsilon][0], collision_numbers[epsilon][1], label=str(epsilon), marker='.',
                     linewidth=1)
        plt.legend()

        # save
        plt.savefig(config.plot_dir + "/" + MODE + "_collisions_over_bitrates_" +
                    str(aggregation) + "_" +
                    str(package_per_bitrate) + ".png",
                    dpi=300)
        plt.close()
        print("generated plot")

        # prepare plot
        plt.figure(figsize=(10, 10))
        plt.xlabel("epsilon value used")
        plt.ylabel("percentage of movies with fingerprint collisions")
        plt.plot(epsilon_collisions.keys(), epsilon_collisions.values(), label=str(MODE), marker='.',
                 linewidth=1)
        plt.plot(other_epsilon_collisions.keys(), other_epsilon_collisions.values(), label=str(OTHER_MODE), marker='.',
                 linewidth=1)
        plt.legend()

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
        plt.plot(total_package_per_bitrate_plot[aggregation][package_per_bitrate][0],
                 total_package_per_bitrate_plot[aggregation][package_per_bitrate][1], label=str(package_per_bitrate),
                 marker='.', linewidth=1)

    # save
    plt.legend()
    plt.savefig(
        config.plot_dir + "/" + MODE + "_collisions_over_bitrates_over_epsilons_over_package_per_bitrate_" + str(
            aggregation
        ) + ".png",
        dpi=300)
    plt.close()
    print("generated plot")
