import sqlite3
import os.path
from python_libs.config import StaticConfig
from python_libs.har_analyzer import HarAnalyzer

config = StaticConfig()
analyzer = HarAnalyzer(config.captures_dir, '.json')

SKIP_FIRST = 50

# get sqlite connection
db_file_name = "listen_data.sqlite"
if os.path.exists(db_file_name):
    os.remove(db_file_name)
connection = sqlite3.connect(db_file_name)

# create tables
connection.execute(
    "CREATE TABLE captures (id INTEGER PRIMARY KEY AUTOINCREMENT, movie_id INTEGER, bitrate INTEGER, created_at TEXT)")

connection.execute(
    "CREATE TABLE packets ("
    "id INTEGER PRIMARY KEY AUTOINCREMENT, "
    "capture_id INTEGER, "
    "url text, "
    "body_size INTEGER, "
    "is_video INTEGER, "
    "range_start INTEGER, "
    "range_end INTEGER, "
    "start_date_time TEXT, "
    "end_date_time TEXT)"
)

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
    for entry in har_entries:
        # exclude audio segments
        if 0.185 * (1024 * 1024) < entry.body_size < 0.195 * (1024 * 1024):
            continue

        start_date_time = None
        if entry.start_date_time is not None:
            start_date_time = entry.start_date_time.isoformat()

        end_date_time = None
        if entry.end_date_time is not None:
            end_date_time = entry.end_date_time.isoformat()
        row_array = [capture_id, entry.url, entry.body_size, entry.is_video, entry.range_start, entry.range_end,
                     start_date_time, end_date_time]
        insert_array.append(row_array)

    # insert har entries to db
    connection.executemany(
        "INSERT INTO packets (capture_id, url, body_size, is_video, range_start, range_end, start_date_time, end_date_time) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        insert_array)
    connection.commit()
