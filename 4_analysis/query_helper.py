class QueryHelper:

    def __init__(self, cursor):
        self.cursor = cursor

    def query_matching_movies(self, db_movies, epsilon, packet_table_name, db_packets):
        # packages to bitrate dictionary
        packets_per_bitrate = {}
        current_bitrate = 0
        for db_packet in db_packets:
            if current_bitrate != db_packet[1]:
                current_bitrate = db_packet[1]
                packets_per_bitrate[current_bitrate] = []
            packets_per_bitrate[current_bitrate].append(db_packet[0])

        # check which movies match the fingerprint
        matching_movies = []
        for checked_db_movie in db_movies:
            checked_movie_id = checked_db_movie[0]
            is_valid = False

            # check for each bitrate that enouh packets are found
            for bitrate in packets_per_bitrate.keys():
                parameters = []
                bitrate_sql = ""
                needed_matches = len(packets_per_bitrate[bitrate])
                for packet in packets_per_bitrate[bitrate]:
                    if len(bitrate_sql) > 0:
                        bitrate_sql += " UNION "

                    select_packet_ids = "SELECT id FROM (SELECT p.id as id, ABS(p.body_size - " + str(
                        packet) + ") as abs_size " \
                                  "FROM " + packet_table_name + " p "
                    select_packet_ids += "INNER JOIN captures c ON c.id = p.capture_id " \
                                         "WHERE c.movie_id = ? AND p.body_size >= ? AND p.body_size <= ? " \
                                         "ORDER BY abs_size " \
                                         "LIMIT ?)"

                    bitrate_sql += select_packet_ids
                    parameters.append(checked_movie_id)
                    parameters.append((1 - epsilon) * packet)
                    parameters.append((1 + epsilon) * packet)
                    parameters.append(needed_matches)

                bitrate_sql = "SELECT COUNT(*) FROM (" + bitrate_sql + ")"
                self.cursor.execute(bitrate_sql, parameters)
                number = self.cursor.fetchall()

                # if not enough packets found then not valid
                if number[0][0] < needed_matches:
                    is_valid = False
                    break
                is_valid = True

            # if for all bitrates found then consider movie as possible
            if is_valid:
                matching_movies.append(checked_movie_id)

        return matching_movies

    def bitrate_attack(self, db_bitrates, db_movies, aggregation, epsilon, packet_table_name, package_per_bitrate):
        # create sql to get all packets we "sniffed"
        sql = "SELECT body_size, bitrate FROM ("
        bitrate_sql = ""
        parameters = []
        for db_bitrate in db_bitrates:
            if len(bitrate_sql) > 0:
                bitrate_sql += " UNION "
            bitrate_sql += "SELECT body_size, bitrate FROM (" \
                           "SELECT DISTINCT c.bitrate as bitrate, p.body_size as body_size, p.id " \
                           "FROM packets_" + str(aggregation) + "_continuous p " \
                                                                "INNER JOIN captures c ON c.id = p.capture_id " \
                                                                "WHERE c.id = ? " \
                                                                "ORDER BY p.id " \
                                                                "LIMIT ?)"
            parameters.append(db_bitrate[0])
            parameters.append(package_per_bitrate)
        sql += bitrate_sql + ") ORDER BY bitrate"

        # get available packets
        self.cursor.execute(sql, parameters)
        db_packets = self.cursor.fetchall()

        # ensure we have "sniffed" all needed packets
        if len(db_packets) != len(db_bitrates) * package_per_bitrate:
            return False

        return self.query_matching_movies(db_movies, epsilon, packet_table_name, db_packets)

    def naive_attack(self, db_bitrates, chosen_bitrate_id, db_movies, aggregation, epsilon, packet_table_name,
                     package_per_bitrate):
        # create sql to get all packets we "sniffed"
        sniffed_packets_count = package_per_bitrate * len(db_bitrates)

        parameters = []

        sql = "SELECT body_size, bitrate FROM (" \
              "SELECT DISTINCT c.bitrate as bitrate, p.body_size as body_size, p.id " \
              "FROM packets_" + str(aggregation) + "_continuous p " \
                                                   "INNER JOIN captures c ON c.id = p.capture_id " \
                                                   "WHERE c.id = ? " \
                                                   "ORDER BY p.id " \
                                                   "LIMIT ?)"
        parameters.append(chosen_bitrate_id)
        parameters.append(sniffed_packets_count)

        # get available packets
        self.cursor.execute(sql, parameters)
        db_packets = self.cursor.fetchall()

        # ensure we have "sniffed" all needed packets
        if len(db_packets) != sniffed_packets_count:
            return False

        return self.query_matching_movies(db_movies, epsilon, packet_table_name, db_packets)
