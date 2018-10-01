class strategy_core():

    def __init__(self, parent):

        self.parent = parent
        self.data_grid = self.parent.data_grid

    def run_strategy(self):

        if self.parent.selection_grid['target_coin_multi_fiat']:
            self.calculate_qcx_implied_usdcad()
            self.calculate_qcx_usd_price_in_cad()
            self.calculate_qcx_fx_spread()
            self.calculate_qcx_vs_bfx_arb()

    def calculate_qcx_usd_price_in_cad(self):

        if self.data_grid['qcx_usd'] != 0 and self.data_grid['fx_rate'] != 0:
            self.data_grid['qcx_usd_to_cad'] = self.data_grid['qcx_usd'] * self.data_grid['fx_rate']

    def calculate_qcx_implied_usdcad(self):

        if self.data_grid['qcx_usd'] != 0 and self.data_grid['qcx_cad'] != 0:
            self.data_grid['qcx_implied_fx_rate'] = self.data_grid['qcx_cad'] / self.data_grid['qcx_usd']

    def calculate_qcx_fx_spread(self):

        if self.data_grid['qcx_usd_to_cad'] != 0 and self.data_grid['qcx_cad'] != 0:
            # 'qcx_internal_fx_coin_spread': 0.0, 'qcx_internal_fx_spread': 0
            fx_coin_spread = self.data_grid['qcx_cad'] - self.data_grid['qcx_usd_to_cad']
            fx_spread = int((self.data_grid['qcx_implied_fx_rate'] - self.data_grid['fx_rate']) * 10000)

            self.data_grid['qcx_internal_fx_coin_spread'] = fx_coin_spread
            self.data_grid['qcx_internal_fx_spread'] = fx_spread

    def calculate_qcx_vs_bfx_arb(self):

        if self.data_grid['qcx_cad'] == 0.0 or self.data_grid['bfx_cad'] == 0.0:
            return

        # We start with fiat
        starting_notional = self.parent.selection_grid['target_notional']
        starting_quantity = self.data_grid['coin_quantity']
        # Buy cryptos on BFX
        buy_fee = starting_quantity * (self.parent.settings_grid['FEES']['bfx_ws']['fiat_take'])
        quantity_bought = starting_quantity * (1 - self.parent.settings_grid['FEES']['bfx_ws']['fiat_take'])
        # Transfer over
        transfer_fee = quantity_bought * self.parent.settings_grid['FEES']['qcx_ws']['coin_fund']
        quantity_transfered = quantity_bought * (1 - self.parent.settings_grid['FEES']['qcx_ws']['coin_fund'])
        # Sell cryptos on QCX
        sold_notional = quantity_transfered * self.parent.data_grid['qcx_cad']
        sell_fee = sold_notional * (self.parent.settings_grid['FEES']['qcx_ws']['fiat_take'])
        ending_notional = sold_notional * (1 - self.parent.settings_grid['FEES']['qcx_ws']['fiat_take'])

        print('Starting Notional: ' + str(starting_notional) + ' | Ending Notional: ' + str(ending_notional))