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
        deposit_fee_usd = starting_notional_usd * self.parent.settings_grid['FEES']['bfx_ws']['fiat_fund']      # In USD
        deposit_fee_cad = deposit_fee_usd * self.parent.data_grid['fx_rate']
        deposit_amount  = starting_notional_usd - deposit_fee_usd
        self.parent.fees_grid['bfx_ws']['deposit'] = deposit_fee_cad
        self.parent.balance_fiat_grid['bfx_fiat_amount'] = ('USD', deposit_amount)

        # Calculate BFX USD to Coin Trade           | BUYING COIN -> Use Asks side of the book
        orderbook = self.parent.orderbook_grid['bfx_ws'][target_coin + 'usd']
        trade_amt, trade_cost = self.average_cost_from_book_notional(orderbook['asks'], deposit_amount)
        # Calculate the trading fee
        trade_fee = trade_amt * self.parent.settings_grid['FEES']['bfx_ws']['fiat_take']
        trade_fee_cad = trade_fee * trade_cost * self.parent.data_grid['fx_rate']
        bfx_coin_amt = trade_amt - trade_fee
        self.parent.fees_grid['bfx_ws']['trading'] = trade_fee_cad
        self.parent.balance_fiat_grid['bfx_coin_amount'] = (target_coin, bfx_coin_amt)


        print(trade_amt, trade_cost, trade_fee)


        # Update gui
        self.parent.data_grid['bfx_usd'] = trade_cost
        self.parent.data_grid['bfx_cad'] = trade_cost * self.parent.data_grid['fx_rate']



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