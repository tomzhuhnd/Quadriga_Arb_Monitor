# ======================================================================================== #
# This is a config file for the websocket handler to check variables against               #
# Contains all of the acceptable inputs on request side that is sent to BFX via websocket  #
# ======================================================================================== #

bfx_public_channels = ['ticker', 'trades', 'book']
bfx_trading_pairs = ['tBTCUSD', 'tETHUSD',
                     'fBTC']


bfx_book_pair_precision = {
    'BTCUSD': 'P1',
    'ETHUSD': 'P1'
}

bfx_book_pair_length = {
    'BTCUSD': '25',
    'ETHUSD': '25'
}