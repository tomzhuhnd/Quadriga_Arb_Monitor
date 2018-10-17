import pymysql
import datetime

connection_user = 'tomzhu'
connection_pass = 'Waterl00!'
connection_port = 3306
connection_host = 'localhost'
connection_db   = 'crypto_market_data'

conn = pymysql.connect(
    host=connection_host,
    port=connection_port,
    user=connection_user,
    passwd=connection_pass,
    db=connection_db
)

cursor = conn.cursor()
data = "'{}', ".format(datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))
data += "1, 1, 1, 1.0, True"

query = """
            INSERT INTO exchange_market_prices 
            (timestamp, exchange_id, base_currency_id, quote_currency_id, spot_price, calculated)
            VALUES ({})""".format(data)

# print(query)
#
# cursor.execute(query)
# conn.commit()
# cursor.close()
# conn.close()


# result = cursor.fetchall()
# print(result)

