import matplotlib.pyplot as plt
import json
import os

from python_libs.config import StaticConfig

config = StaticConfig()


def remove(folder):
    json_files = [pos_json for pos_json in os.listdir(folder) if pos_json.endswith('.json')]
    json_files = sorted(json_files)

    seenDic = {}

    for file in json_files:
        splits = file.split("_")

        movieId = int(splits[0])
        configId = int(splits[1])
        versionId = splits[len(splits) - 1]

        # only keep newest file for each movie, config, version
        seenDic.setdefault(movieId, {})
        seenDic[movieId].setdefault(configId, {})
        if versionId in seenDic[movieId][configId]:
            os.remove(folder + "/" + seenDic[movieId][configId])

        seenDic[movieId][configId] = file

remove(config.captures_dir)
remove(config.attack_dir)