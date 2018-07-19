# plots the possible packet sizes for each aggregation level
# plots boxplots of the package sizes at each aggregation level

import matplotlib.pyplot as plt
import sqlite3

from python_libs.config import StaticConfig, Inventory

config = StaticConfig()
inventory = Inventory()

START_AGGREGATION = 1
LAST_AGGREGATION = 10

# get sqlite connection
db_file_name = "plot_data.sqlite"
connection = sqlite3.connect(db_file_name)
cursor = connection.cursor()

box_plot_data = []
for aggregation in range(START_AGGREGATION, LAST_AGGREGATION + 1):
    print("for aggregation " + str(aggregation))

    cursor.execute("SELECT body_size FROM packets WHERE aggregation = ?", [aggregation])

    sizes = []
    db_packets = cursor.fetchall()
    for db_packet in db_packets:
        sizes.append(db_packet[0] / (1024 * 1024))

    box_plot_data.append(sizes)

    sizes = sorted(sizes)

    # prepare plot
    fig = plt.figure()
    plt.ylabel("size of " + str(aggregation) + "-package in megabytes")
    plt.xlabel(str(aggregation) + "-packages ordered by size")
    plt.plot(sizes)

    # save.
    plt.savefig(config.plot_dir + "/size_" + str(aggregation) + ".png", dpi=300)
    plt.close()

# prepare plot
fig = plt.figure()
plt.ylabel("size of n-packages in megabytes")
plt.xlabel("aggregation level n of packages")
plt.boxplot(box_plot_data)

# save
plt.savefig(config.plot_dir + "/size_boxplot.png", dpi=300)
plt.close()
print()
