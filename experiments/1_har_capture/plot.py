import matplotlib.pyplot as plt
import json
import os

captures_dir = "capture"
capture_version = "1"
plot_dir = "plot"

json_files = [pos_json for pos_json in os.listdir(captures_dir) if pos_json.endswith("_" + capture_version + '.json')]

json_files = sorted(json_files)

sizePerFile = {}

for file in json_files:
    sizeX = [0]
    sizeY = [0]
    bandwidthY = []
    bandwidthX = []

    with open(captures_dir + "/" + file, 'r') as myfile:
        data = myfile.read()

    content = json.loads(data)
    for entry in content["log"]["entries"]:
        url = entry["request"]["url"]
        size = entry["response"]["bodySize"]
        if "video.net/range/" in url:
            lastIndex = url.rindex("/range")
            lastPart = url[(lastIndex + len("/range") + 1):]
            if "?" in lastPart:
                lastPart = lastPart[:lastPart.index("?")]

            range = lastPart.split("-")

            # xAxis.append(int(range[0]))
            sizeX.append(int(range[1]))
            sizeY.append(size)

            total_range = int(range[1]) - int(range[0])
            bandwidth = size / total_range

            plt.plot([int(range[0]), int(range[1])], [bandwidth, bandwidth], 'ro-')

    plt.savefig(plot_dir + "/" + file + "_bandwidth.png")
    plt.close()

    plt.plot(sizeX, sizeY, "ro")
    # plt.grid(True)
    # plt.figure(figsize=(10, 10))
    # plt.annotate(..., fontsize='xx-small', ...)
    # plt.axis([0, 6, 0, 20])
    plt.savefig(plot_dir + "/" + file + "_size.png")
    plt.close()
