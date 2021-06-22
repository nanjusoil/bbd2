class Strategy():
    # option setting needed
    def __setitem__(self, key, value):
        self.options[key] = value

    # option setting needed
    def __getitem__(self, key):
        return self.options.get(key, '')

    def __init__(self):
        # strategy property
        self.subscribedBooks = {
            'Binance': {
                'pairs': ['ADA-USDT'],
            },
        }
        self.period = 10 * 60
        self.options = {}

        # user defined class attribute
        self.last_type = 'sell'
        self.last_cross_status = None
        self.close_price_trace = np.array([])
        self.high_price_trace = np.array([])
        self.low_price_trace = np.array([])

        self.ma_long = 10
        self.ma_short = 5
        self.UP = 1
        self.DOWN = 2

        self.buy_price = []
        self.start_amount = None


    def on_order_state_change(self,  order):
        pass
        # Log("on order state change message: " + str(order) + " order price: " + str(order["price"]))

    # called every self.period
    def trade(self, information):
        exchange = list(information['candles'])[0]
        pair = list(information['candles'][exchange])[0]
        target_currency = pair.split('-')[0]  #ETH
        base_currency = pair.split('-')[1]  #USDT
        base_currency_amount = self['assets'][exchange][base_currency] 
        target_currency_amount = self['assets'][exchange][target_currency] 
        if( self.start_amount == None):
            self.start_amount = base_currency_amount

        # add latest price into trace
        close_price = information['candles'][exchange][pair][0]['close']
        high_price = information['candles'][exchange][pair][0]['high']
        low_price = information['candles'][exchange][pair][0]['low']


        self.close_price_trace = np.append(self.close_price_trace, [float(close_price)])
        self.high_price_trace = np.append(self.high_price_trace, [float(high_price)])
        self.low_price_trace = np.append(self.low_price_trace, [float(low_price)])

        sar = talib.SAR(self.high_price_trace ,self.low_price_trace, acceleration=float(self['acceleration']), maximum=float(self['maximum']) )

        signal_bull = np.where((self.close_price_trace > sar) &
                                   (np.roll(self.close_price_trace, 1) < np.roll(sar, 1)) , 1, 0)

        signal_bear = np.where( (self.close_price_trace < sar) &
                                   (np.roll(self.close_price_trace, 1) > np.roll(sar, 1)), 1, 0)
        if(self.close_price_trace .shape[0] % 5== 0 ):
            if(signal_bear[-1] == 1):
                self.buy_price.append(close_price)
                self.buy_price.sort()
                return [
                    {
                        'exchange': exchange,
                        'amount': float(self.start_amount  * 0.2 )/ close_price,
                        'price': -1,
                        'type': 'MARKET',
                        'pair': pair,
                    }
                ]
            elif(len(self.buy_price ) > 0 and self.buy_price[-1] * float(self['sell_rate']) < close_price):
                self.buy_price = []
                return [
                    {
                        'exchange': exchange,
                        'amount': -target_currency_amount,
                        'price': -1,
                        'type': 'MARKET',
                        'pair': pair,
                    }
                ]
            elif( len(self.buy_price ) > 0 and  signal_bull[-1] == 1 and float(self.buy_price[0]) < close_price):
                self.buy_price.pop(0)
                return [
                    {
                        'exchange': exchange,
                        'amount': -target_currency_amount * 0.25,
                        'price': -1,
                        'type': 'MARKET',
                        'pair': pair,
                    }
                ]


        return []
