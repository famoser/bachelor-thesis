import matplotlib.pyplot as plt
import json
import os

from python_libs.config import StaticConfig
from python_libs.har_analyzer import HarAnalyzer

config = StaticConfig()
analyzer = HarAnalyzer(config.capture_dir, str(config.capture_version) + '.json')

# plot
for file in analyzer.har_entry_dict():
    sizeX = [0]
    sizeY = [0]
    bandwidthY = []
    bandwidthX = []

    for entry in analyzer.har_entry_dict()[file]:
        if entry.is_video:
            # xAxis.append(int(range[0]))
            sizeX.append(entry.range_end)
            sizeY.append(entry.body_size)

            bandwidth = entry.body_size / entry.get_length()

            plt.plot([entry.range_start, entry.range_end], [bandwidth, bandwidth], 'ro-')

    # parse movie id
    splits = file.split("_")
    movie_id = int(splits[0])

    # save bandwidth analysis (plotted in loop)
    plt.savefig(plot_dir + "/" + str(movie_id) + "_bandwidth.png")
    plt.close()

    # save total sizes
    plt.plot(sizeX, sizeY, "ro")
    plt.savefig(plot_dir + "/" + str(movie_id) + "_size.png")
    plt.close()
