import sqlite3
import os.path
from python_libs.config import StaticConfig
from python_libs.har_analyzer import HarAnalyzer

config = StaticConfig()
analyzer = HarAnalyzer(config.captures_dir, '.json')

START_AGGREGATION = 0
END_AGGREGATION = 3

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

    for aggregation in range(START_AGGREGATION, END_AGGREGATION):
        for i in range(0, len(har_entries)):
            start_entry = har_entries[i]
            if i + aggregation >= len(har_entries):
                continue

            end_entry = har_entries[i + aggregation]

            row_array = [capture_id, end_entry.range_end - start_entry.range_start, aggregation]
            insert_array.append(row_array)

        # insert har entries to db
        connection.executemany(
            "INSERT INTO packets "
            "(capture_id, body_size, aggregation) "
            "VALUES "
            "(?, ?, ?)",
            insert_array)
        connection.commit()
