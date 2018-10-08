class strategy_core():

    def __init__(self, parent):

        self.parent = parent

    def run_strategy(self):

        self.run_bfx_to_usd_cad_arb()


        # if self.parent.selection_grid['target_coin_multi_fiat']:
        #     self.calculate_qcx_implied_usdcad()
        #     self.calculate_qcx_usd_price_in_cad()
        #     self.calculate_qcx_fx_spread()
        #     self.calculate_qcx_vs_bfx_arb()

    def run_bfx_to_usd_cad_arb(self):

        if (
                self.parent.data_grid['fx_rate'] == 0 or self.parent.selection_grid['target_coin'] == '-' or
                self.parent.selection_grid['target_notional'] == 0.0 or not self.parent.orderbook_grid['bfx_ws']
        ):
            return

        target_coin = self.parent.selection_grid['target_coin'].lower()

        starting_notional_cad = self.parent.selection_grid['target_notional']
        self.parent.balance_fiat_grid['starting_cad'] = ('CAD', starting_notional_cad)

        # Calculate FX Conversion
        starting_notional_usd = starting_notional_cad / self.parent.data_grid['fx_rate']
        self.parent.balance_fiat_grid['starting_usd'] = ('USD', starting_notional_usd)

        # Calculate Deposit to BFX Fee
        bfx_deposit_fee_usd = starting_notional_usd * self.parent.settings_grid['FEES']['bfx_ws']['fiat_fund']
        bfx_deposit_fee_cad = bfx_deposit_fee_usd * self.parent.data_grid['fx_rate']
        bfx_deposit_amount  = starting_notional_usd - bfx_deposit_fee_usd
        self.parent.fees_grid['bfx_ws']['deposit'] = bfx_deposit_fee_cad
        self.parent.balance_fiat_grid['bfx_fiat_amount'] = ('USD', bfx_deposit_amount)

        # Calculate BFX USD to Coin Trade           | BUYING COIN -> Use Asks side of the book
        orderbook = self.parent.orderbook_grid['bfx_ws'][target_coin + 'usd']
        bfx_trade_amt, bfx_trade_cost = self.average_cost_from_book_notional(orderbook['asks'], bfx_deposit_amount)
        # Calculate the trading fee
        bfx_trade_fee = bfx_trade_amt * self.parent.settings_grid['FEES']['bfx_ws']['fiat_take']
        bfx_trade_fee_cad = bfx_trade_fee * bfx_trade_cost * self.parent.data_grid['fx_rate']       # Convert into CAD
        bfx_coin_amt = bfx_trade_amt - bfx_trade_fee
        self.parent.fees_grid['bfx_ws']['trading'] = bfx_trade_fee_cad
        self.parent.balance_coin_grid['bfx_coin_amount'] = (target_coin, bfx_coin_amt)

        # BFX coin balance transfered to QCX
        bfx_transfer_fee = bfx_coin_amt * self.parent.settings_grid['FEES']['bfx_ws']['coin_draw']      # In coin amount
        bfx_transfer_fee_cad = bfx_transfer_fee * bfx_trade_cost * self.parent.data_grid['fx_rate']             # In CAD
        self.parent.fees_grid['bfx_ws']['withdraw'] = bfx_transfer_fee_cad
        qcx_coin_amt = bfx_coin_amt - bfx_transfer_fee
        self.parent.balance_coin_grid['qcx_coin_amount'] = (target_coin, qcx_coin_amt)

        # Calculate QCX BTC to CAD Trade             | SELLING COIN -> Use Bids side of the book
        # Calulate the equivalent cost in USD for comparison purposes
        if target_coin + 'usd' in self.parent.orderbook_grid['qcx_ws']:
            orderbook_usd = self.parent.orderbook_grid['qcx_ws'][target_coin + 'usd']
            qcx_trade_amt_usd, qcx_trade_cost_usd = self.average_cost_from_book_quantity(orderbook_usd['bids'],
                                                                                     qcx_coin_amt)
        else:
            qcx_trade_cost_usd = None

        # Calculate cost in CAD
        orderbook = self.parent.orderbook_grid['qcx_ws'][target_coin + 'cad']
        qcx_trade_amt, qcx_trade_cost = self.average_cost_from_book_quantity(orderbook['bids'], qcx_coin_amt)
        qcx_trade_amt = qcx_trade_amt * qcx_trade_cost
        # Calculate the trading fee
        qcx_trade_fee = qcx_trade_amt * self.parent.settings_grid['FEES']['qcx_ws']['fiat_take']
        self.parent.fees_grid['qcx_ws']['trading'] = qcx_trade_fee
        qcx_fiat_amt = qcx_trade_amt - qcx_trade_fee
        self.parent.balance_fiat_grid['qcx_fiat_amount'] = ('CAD', qcx_fiat_amt)

        # Calculate the cost to take out the fiat
        qcx_withdraw_fee = qcx_fiat_amt * self.parent.settings_grid['FEES']['qcx_ws']['fiat_draw']
        self.parent.fees_grid['qcx_ws']['withdraw'] = qcx_withdraw_fee
        ending_notional_cad = qcx_fiat_amt - qcx_withdraw_fee
        self.parent.balance_fiat_grid['ending_cad'] = ('CAD', ending_notional_cad)

        # GUI Display
        self.parent.data_grid['qcx_cad'] = qcx_trade_cost
        if qcx_trade_cost_usd is not None:
            self.parent.data_grid['qcx_usd'] = qcx_trade_cost_usd
        self.parent.data_grid['qcx_usd_to_cad'] = qcx_trade_cost_usd * self.parent.data_grid['fx_rate']
        self.parent.data_grid['qcx_implied_fx_rate'] = qcx_trade_cost / qcx_trade_cost_usd
        self.parent.data_grid['qcx_internal_fx_coin_spread'] = qcx_trade_cost - self.parent.data_grid['qcx_usd_to_cad']
        qcx_internal_fx_spread = (self.parent.data_grid['qcx_implied_fx_rate'] - self.parent.data_grid['fx_rate'])
        self.parent.data_grid['qcx_internal_fx_spread'] = round(qcx_internal_fx_spread * 10000, 2)
        self.parent.data_grid['bfx_usd'] = bfx_trade_cost
        self.parent.data_grid['bfx_cad'] = bfx_trade_cost * self.parent.data_grid['fx_rate']
        self.parent.data_grid['arb_spread'] = ending_notional_cad - starting_notional_cad
        self.parent.data_grid['arb_return'] = round((ending_notional_cad / starting_notional_cad) - 1, 6) * 100

    def average_cost_from_book_quantity(self, order_book, quantity):

        target_quantity = quantity

        total_coin = 0.0
        total_notional = 0.0

        for level in order_book:
            price = float(level)
            coins = float(order_book[level])
            if coins + total_coin >= target_quantity:
                total_notional += (target_quantity - total_coin) * price
                total_coin = target_quantity
                break
            else:
                total_notional += price * coins
                total_coin += coins

        return total_coin, total_notional / total_coin

    def average_cost_from_book_notional(self, order_book, notional):

        # Assumes the notional is already pre-converted
        target_notional = notional

        total_coin = 0.0
        total_notional = 0.0

        for level in order_book:
            price = float(level)
            coins = float(order_book[level])
            level_notional = price * coins
            if total_notional + level_notional >= target_notional:
                total_coin += (target_notional - total_notional) / price
                total_notional += target_notional - total_notional
                break
            else:
                total_notional += level_notional
                total_coin += coins

        return total_coin, total_notional / total_coin