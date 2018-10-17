import pymysql

connection_user = 'tomzhu'
connection_pass = 'Waterl00!'
connection_port = 3306
connection_host = 'localhost'
connection_db   = 'crypto_market_data'

def upload_exchange_market_prices(data):

    query = 'INSERT INTO exchange_market_prices \n(timestamp, exchange_id, base_currency_id, quote_currency_id, '
    query += 'spot_price, calculated, computed, price_type, computed_notional) VALUES\n'
    for row in data:
        query += '(' + str(row[:-1])[1:-1] + ', ' + str(row[-1]) + '),\n'

    query = query[:-2]
    print(query)