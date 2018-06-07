import sqlite3
import os.path
from python_libs.config import StaticConfig
from python_libs.har_analyzer import HarAnalyzer

config = StaticConfig()
analyzer = HarAnalyzer(config.captures_dir, '.json')

START_AGGREGATION = 0
END_AGGREGATION = 20

# get sqlite connection
db_file_name = config.captures_dir + "/data.sqlite"
if os.path.exists(db_file_name):
    os.remove(db_file_name)
connection = sqlite3.connect(db_file_name)

# create tables
connection.execute(
    "CREATE TABLE captures ("
    "id INTEGER PRIMARY KEY AUTOINCREMENT, "
    "movie_id INTEGER, "
    "bitrate INTEGER, "
    "created_at TEXT)")

connection.execute(
    "CREATE TABLE packets ("
    "id INTEGER PRIMARY KEY AUTOINCREMENT, "
    "capture_id INTEGER, "
    "body_size INTEGER, "
    "aggregation INTEGER)")

connection.commit()

# create lookup like lookup[movie_id][bandwidth] = video_size
for file_name in analyzer.get_file_names():
    # analyze file name
    splits = file_name.split("_")
    movie_id = int(splits[0])
    bitrate = int(splits[1])
    created_at = splits[2] + ":" + splits[3] + ":" + splits[4].replace(".json", "")

    # insert capture info & get id
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO captures (movie_id, bitrate, created_at) VALUES (?, ?, ?)",
        [movie_id, bitrate, created_at])
    capture_id = cursor.lastrowid
    connection.commit()

    # transform har entries to sqlite entry
    insert_array = []
    har_entries = analyzer.get_har_entries_dict()[file_name]

    # remove all non video entries
    har_entries = [entry for entry in har_entries if entry.is_video]

    # sort by request order
    har_entries = sorted(har_entries, key=lambda x: x.range_start)

    # keep only size
    sizes = [entry.body_size for entry in har_entries]

    # aggregate
    for aggregation in range(START_AGGREGATION, END_AGGREGATION):
        for i in range(0, len(sizes)):
            if i + aggregation >= len(sizes):
                continue

            size = 0
            for j in range(0, aggregation):
                size += sizes[i + j]

            row_array = [capture_id, size, aggregation]
            insert_array.append(row_array)

        # insert har entries to db
        connection.executemany(
            "INSERT INTO packets "
            "(capture_id, body_size, aggregation) "
            "VALUES "
            "(?, ?, ?)",
            insert_array)
        connection.commit()

        print("done for " + str(movie_id) + " at bitrate " + str(bitrate) + " (" + str(aggregation) + ")")