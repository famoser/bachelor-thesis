# this first queries the expected packets to be captured by an attacker looking at all different bitrates
# then it queries the database with distored package sizes and checking for the amount of matches


import matplotlib.pyplot as plt
import sqlite3

from python_libs.config import StaticConfig, Inventory

config = StaticConfig()
inventory = Inventory()

START_AGGREGATION = 10
LAST_AGGREGATION = 10

EPSILON_STEP = 0.0025
LAST_EPSILON = 0.05

PACKAGE_PER_BITRATE = 3

MAX_MOVIES = 100

# get sqlite connection
db_file_name = "plot_data.sqlite"
connection = sqlite3.connect(db_file_name)
cursor = connection.cursor()

total_plot = {}

for aggregation in range(START_AGGREGATION, LAST_AGGREGATION + 1):
    packet_table_name = "packets_" + str(aggregation) + "_continuous"

    current_epsilon_multiplication = 0
    epsilon = current_epsilon_multiplication * EPSILON_STEP

    epsilon_collisions = {}

    while epsilon <= LAST_EPSILON:
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
            bitrate_sql = ""
            parameters = []
            for db_bitrate in db_bitrates:
                if len(bitrate_sql) > 0:
                    bitrate_sql += " UNION "
                bitrate_sql += "SELECT body_size, bitrate FROM (" \
                               "SELECT DISTINCT c.bitrate as bitrate, p.body_size as body_size, p.id " \
                               "FROM packets_" + str(aggregation) + "_continuous p " \
                                                                    "INNER JOIN captures c ON c.id = p.capture_id " \
                                                                    "WHERE c.id = ? " \
                                                                    "ORDER BY p.id " \
                                                                    "LIMIT ?)"
                parameters.append(db_bitrate[0])
                parameters.append(PACKAGE_PER_BITRATE)
            sql += bitrate_sql + ") ORDER BY bitrate"

            # get available packets
            cursor.execute(sql, parameters)
            db_packets = cursor.fetchall()

            # ensure we have "sniffed" all needed packets
            if len(db_packets) != len(db_bitrates) * PACKAGE_PER_BITRATE:
                print("skipped because not enough packages per bitrate")
                continue

            # packages to bitrate dictionary
            packets_per_bitrate = {}
            current_bitrate = 0
            for db_packet in db_packets:
                if current_bitrate != db_packet[1]:
                    current_bitrate = db_packet[1]
                    packets_per_bitrate[current_bitrate] = []
                packets_per_bitrate[current_bitrate].append(db_packet[0])

            matching_movies = []

            # check which movies match the fingerprint
            for checked_db_movie in db_movies:
                checked_movie_id = checked_db_movie[0]
                is_valid = False

                # check for each bitrate that enouh packets are found
                for bitrate in packets_per_bitrate.keys():
                    parameters = []
                    bitrate_sql = ""
                    needed_matches = len(packets_per_bitrate[bitrate])
                    for packet in packets_per_bitrate[bitrate]:
                        if len(bitrate_sql) > 0:
                            bitrate_sql += " UNION "

                        select_packet_ids = "SELECT id FROM (SELECT p.id as id, ABS(p.body_size - " + str(
                            packet) + ") as abs_size " \
                                      "FROM " + packet_table_name + " p "
                        select_packet_ids += "INNER JOIN captures c ON c.id = p.capture_id " \
                                             "WHERE c.movie_id = ? AND p.body_size >= ? AND p.body_size <= ? " \
                                             "ORDER BY abs_size " \
                                             "LIMIT ?)"

                        bitrate_sql += select_packet_ids
                        parameters.append(checked_movie_id)
                        parameters.append((1 - epsilon) * packet)
                        parameters.append((1 + epsilon) * packet)
                        parameters.append(needed_matches)

                    bitrate_sql = "SELECT COUNT(*) FROM (" + bitrate_sql + ")"
                    cursor.execute(bitrate_sql, parameters)
                    number = cursor.fetchall()

                    # if not enough packets found then not valid
                    if number[0][0] < needed_matches:
                        is_valid = False
                        break
                    is_valid = True

                # if for all bitrates found then consider movie as possible
                if is_valid:
                    matching_movies.append(checked_movie_id)

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
                print("collision found for " + str(movie_id) + " with " + ', '.join(str(x) for x in conflict_movies))
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
            movies_checked) + " checked movies with " + str(PACKAGE_PER_BITRATE) + " packages per bitrate")
        plt.ylabel("how often this happened")
        plt.plot(figure_collisions.keys(), figure_collisions.values(), label=str(aggregation), marker='.', linewidth=1)

        # save
        plt.savefig(config.plot_dir + "/collisions_over_bitrates_" +
                    str(aggregation) + "_" +
                    str(epsilon) + "_" +
                    str(PACKAGE_PER_BITRATE) + ".png",
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
    plt.plot(epsilon_collisions.keys(), epsilon_collisions.values(), label=str(aggregation), marker='.', linewidth=1)

    # save
    plt.savefig(config.plot_dir + "/collisions_over_bitrates_over_epsilons_" +
                str(aggregation) + "_" +
                str(PACKAGE_PER_BITRATE) + ".png",
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
    plt.plot(total_plot[aggregation][0], total_plot[aggregation][1], label=str(aggregation), marker='.', linewidth=1)

# save
plt.savefig(config.plot_dir + "/collisions_over_bitrates_over_epsilons_" + str(PACKAGE_PER_BITRATE) + ".png", dpi=300)
plt.close()
print("generated plot")
