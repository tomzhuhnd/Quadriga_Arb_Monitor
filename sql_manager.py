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

    run_upload_query(query)


def upload_arbitrage_statistics(data):

    query = 'INSERT INTO arb_statistics_buy_transfer_sell \n'
    query += '(timestamp, start_exchange_id, end_exchange_id, start_exchange_side, end_exchange_side, ' \
             'start_exchange_base_ccy_id, start_exchange_quote_ccy_id, end_exchange_base_ccy_id, ' \
             'end_exchange_quote_ccy_id, start_exchange_price, end_exchange_price, arbitrage_notional, ' \
             'estimated_profit) VALUES \n'
    for row in data:
        query += '(' + str(row)[1:-1] + '),\n'

    query = query[:-2]

    run_upload_query(query)


def run_upload_query(query):

    connection = pymysql.connect(
        host=connection_host, port=connection_port, user=connection_user, passwd=connection_pass, db=connection_db
    )

    cursor = connection.cursor()
    cursor.execute(query)
    cursor.close()
    connection.commit()
    cursor.close()
    connection.close()
