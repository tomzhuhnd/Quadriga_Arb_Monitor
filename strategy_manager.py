class strategy_core():

    def __init__(self, parent):

        self.parent = parent
        self.data_grid = self.parent.data_grid

    def run_strategy(self):

        if self.parent.selection_grid['target_coin_multi_fiat']:
            self.calculate_qcx_implied_usdcad()
            self.calculate_qcx_usd_price_in_cad()
            self.calculate_qcx_fx_spread()

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
