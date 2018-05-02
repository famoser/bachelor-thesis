import matplotlib.pyplot as plt
import hashlib

from python_libs.config import StaticConfig
from python_libs.har_analyzer import HarAnalyzer

config = StaticConfig()
analyzer = HarAnalyzer(config.attack_dir, str(config.attack_version) + '.json')

thorughput_lookup = {}
packet_count_lookup = {}

# create lookup like lookup[movie_id][bandwidth] = video_size
for file_name in analyzer.get_file_names():
    # analyze file name
    splits = file_name.split("_")
    movie_id = int(splits[0])
    bandwidth = int(splits[1])

    capture_statistics = analyzer.get_capture_statistics()[file_name]

    # ignore value if its too small to be possible
    value = capture_statistics.get_throughput()
    if value < 1000:
        continue

    # add to big result dictionary
    thorughput_lookup.setdefault(movie_id, {})
    thorughput_lookup[movie_id].setdefault(bandwidth, [])
    thorughput_lookup[movie_id][bandwidth].append(value)

    packet_count_lookup.setdefault(movie_id, {})
    packet_count_lookup[movie_id].setdefault(bandwidth, [])
    packet_count_lookup[movie_id][bandwidth].append(capture_statistics.get_packet_count)

# plot bandwidth, video_size per movie
for movie_id in thorughput_lookup:
    x = []
    y = []

    for bandwidth in thorughput_lookup[movie_id]:
        bandwidths = thorughput_lookup[movie_id][bandwidth]
        packet_counts = packet_count_lookup[movie_id][bandwidth]
        if len(thorughput_lookup[movie_id][bandwidth]) > 0:
            for entry in bandwidths:
                x.append(bandwidth)
                y.append(entry)

    # plot
    plt.plot(x, y, "ro")
    plt.savefig(config.plot_dir + "/" + str(movie_id) + "_attack_bandwidth.png")
    plt.close()

# all together
legendIdentifier = []
legendValue = []

# plot bandwidth, video_size per movie in single plot
# create single subplot
fig, axes = plt.subplots(1, 1)
movie_ids = ""
for movie_id in thorughput_lookup:
    x = []
    y = []

    for bandwidth in thorughput_lookup[movie_id]:
        for entry in thorughput_lookup[movie_id][bandwidth]:
            if entry < 150000:
                x.append(bandwidth)
                y.append(entry)

    # plot with label = movie_id
    axes.plot(x, y, label=str(movie_id), marker='.', linewidth=0)
    movie_ids += str(movie_id)

# place label to the right
plt.legend(loc=(1.04, 0))
plt.tight_layout()
plt.subplots_adjust(right=0.75)

# save
filename = hashlib.md5(movie_ids.encode()).hexdigest()
plt.savefig(config.plot_dir + "/" + filename + "_attack.png")
plt.close()