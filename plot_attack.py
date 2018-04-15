import matplotlib.pyplot as plt
import json
import os

from python_libs.config import StaticConfig

config = StaticConfig()

json_files = [pos_json for pos_json in os.listdir(config.attack_dir) if
              pos_json.endswith("_" + str(config.attack_version) + '.json')]

json_files = sorted(json_files)

movieLookup = {}

# calculate size per file
for file in json_files:
    # calculate size per file
    with open(config.attack_dir + "/" + file, 'r') as myfile:
        data = myfile.read()

    content = json.loads(data)
    file_size = 0
    for entry in content["log"]["entries"]:
        url = entry["request"]["url"]
        size = entry["response"]["bodySize"]
        if "video.net/range/" in url:
            file_size += size

    # analyze file name
    splits = file.split("_")

    movieId = int(splits[0])
    bandwidth = int(splits[1])

    # add to big result dictionary
    movieLookup.setdefault(movieId, {})
    movieLookup[movieId].setdefault(bandwidth, [])
    movieLookup[movieId][bandwidth].append(file_size)

# individual plots
for movieId in movieLookup:
    x = []
    y = []

    for bandwidth in movieLookup[movieId]:
        for entry in movieLookup[movieId][bandwidth]:
            x.append(bandwidth)
            y.append(entry)

    # plot
    plt.plot(x, y, "ro")
    plt.savefig(config.plot_dir + "/" + str(movieId) + "_attack.png")
    plt.close()

# all together
legendIdentifier = []
legendValue = []

fig, axes = plt.subplots(1)
for movieId in movieLookup:
    x = []
    y = []

    for bandwidth in movieLookup[movieId]:
        for entry in movieLookup[movieId][bandwidth]:
            x.append(bandwidth)
            y.append(entry)

    # plot
    axes.plot(x, y, label=str(movieId), marker='.', linewidth=0)

plt.legend(loc=(1.04, 0))
plt.tight_layout()
plt.subplots_adjust(right=0.75)
plt.savefig(config.plot_dir + "/all_attack.png")
plt.close()
