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

box_plot_data = []
for aggregation in range(START_AGGREGATION, LAST_AGGREGATION + 1):
    print("for aggregation " + str(aggregation))

    cursor.execute("SELECT body_size FROM packets WHERE aggregation = ?", [aggregation])

    sizes = []
    db_packets = cursor.fetchall()
    for db_packet in db_packets:
        sizes.append(db_packet[0])

    box_plot_data.append(sizes)

    sizes = sorted(sizes)

    # prepare plot
    fig = plt.figure(figsize=(10, 10))
    plt.ylabel("size of packet")
    plt.xlabel("# of packet (sorted)")
    plt.plot(sizes)

    # save
    plt.savefig(config.plot_dir + "/" + str(aggregation) + "_packet_size.png", dpi=300)
    plt.close()
    print()


# prepare plot
fig = plt.figure(figsize=(10, 10))
plt.ylabel("size of packet")
plt.xlabel("aggregation")
plt.boxplot(box_plot_data)

# save
plt.savefig(config.plot_dir + "/boxplot_packet_sizes.png", dpi=300)
plt.close()
print()