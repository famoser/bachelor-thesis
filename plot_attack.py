import matplotlib.pyplot as plt
import json
import os

from python_libs.config import StaticConfig
from python_libs.har_analyzer import HarAnalyzer

config = StaticConfig()
analyzer = HarAnalyzer(config.attack_dir, str(config.attack_version) + '.json')

lookup = {}

# create lookup like lookup[movie_id][bandwidth] = video_size
for file in analyzer.video_size_dict():
    # analyze file name
    splits = file.split("_")
    movie_id = int(splits[0])
    bandwidth = int(splits[1])

    # add to big result dictionary
    lookup.setdefault(movie_id, {})
    lookup[movie_id].setdefault(bandwidth, [])
    lookup[movie_id][bandwidth].append(analyzer.video_size_dict()[file])

# plot bandwidth, video_size per movie
for movie_id in lookup:
    x = []
    y = []

    for bandwidth in lookup[movie_id]:
        for entry in lookup[movie_id][bandwidth]:
            x.append(bandwidth)
            y.append(entry)

    # plot
    plt.plot(x, y, "ro")
    plt.savefig(config.plot_dir + "/" + str(movie_id) + "_attack.png")
    plt.close()

# all together
legendIdentifier = []
legendValue = []

# plot bandwidth, video_size per movie in single plot
# create single subplot
fig, axes = plt.subplots(1, 1)
for movie_id in lookup:
    x = []
    y = []

    for bandwidth in lookup[movie_id]:
        for entry in lookup[movie_id][bandwidth]:
            x.append(bandwidth)
            y.append(entry)

    # plot with label = movie_id
    axes.plot(x, y, label=str(movie_id), marker='.', linewidth=0)

# place label to the right
plt.legend(loc=(1.04, 0))
plt.tight_layout()
plt.subplots_adjust(right=0.75)

# save
plt.savefig(config.plot_dir + "/all_attack.png")
plt.close()