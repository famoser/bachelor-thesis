import sqlite3
import os.path
from python_libs.config import StaticConfig
from python_libs.har_analyzer import HarAnalyzer

config = StaticConfig()
analyzer = HarAnalyzer(config.captures_dir, '.json')

START_AGGREGATION = 1
LAST_AGGREGATION = 10

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
    "aggregation INTEGER,"
    "continuous BOOLEAN)")

connection.commit()

burned = {}

# create lookup like lookup[movie_id][bandwidth] = video_size
for file_name in analyzer.get_file_names():
    # analyze file name
    splits = file_name.split("_")
    movie_id = int(splits[0])
    bitrate = int(splits[1])
    created_at = splits[2] + ":" + splits[3] + ":" + splits[4].replace(".json", "")

    # do not insert two times
    if movie_id in burned and bitrate in burned[movie_id]:
        continue

    # add to burned to avoid double insertion
    if movie_id not in burned:
        burned[movie_id] = []
    burned[movie_id].append(bitrate)

    # insert capture info & get id
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO captures (movie_id, bitrate, created_at) VALUES (?, ?, ?)",
        [movie_id, bitrate, created_at])
    capture_id = cursor.lastrowid
    connection.commit()

    # transform har entries to sqlite entry
    insert_array = []
    sizes = analyzer.get_ordered_sizes(analyzer.get_har_entries_dict()[file_name])

    # aggregate
    for aggregation in range(START_AGGREGATION, LAST_AGGREGATION + 1):
        # all aggregations
        for i in range(0, len(sizes)):
            if i + aggregation > len(sizes):
                continue

            size = 0
            for j in range(0, aggregation):
                size += sizes[i + j]

            insert_array.append([capture_id, size, aggregation, False])

        # continuous aggregation
        current_aggregation = 0
        current_value = 0
        for size in sizes:
            current_aggregation += 1
            current_value += size
            if current_aggregation == aggregation:
                insert_array.append([capture_id, current_value, aggregation, True])
                current_aggregation = 0
                current_value = 0

        # insert har entries to db
        connection.executemany(
            "INSERT INTO packets "
            "(capture_id, body_size, aggregation, continuous) "
            "VALUES "
            "(?, ?, ?, ?)",
            insert_array)
        connection.commit()

        print("done for " + str(movie_id) + " at bitrate " + str(bitrate) + " (" + str(aggregation) + ")")

connection.execute("CREATE INDEX packet_body_size ON packets (body_size)")