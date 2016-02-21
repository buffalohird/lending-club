import pandas as pd
import numpy as np
from collections import defaultdict
from loan import Loan
from investor import Investor

class Backtest():
    def __init__(self, sdate, edate, buy_solver, db, buy_size=25.0):
        self.investor = Investor(1000)
        self.month = pd.Period(sdate, freq='M')
        self.end_month = pd.Period(edate, freq='M')
        self.buy_solver = buy_solver
        self.db = db
        self.buy_size = buy_size
        
        self.stats = defaultdict(dict)
        self.loans = pd.DataFrame()
        self.current_loans = dict()
    
    def solve_month(self):
        self.investor.get_payments()
        new_loans, available_new_loans = self.buy()
        
        self.loans = pd.concat([self.loans, new_loans], axis=0)
        self.current_loans['self.month'] = [loan for loan in self.investor.loans]
        
        self.stats['loans added'][self.month] = len(new_loans)
        self.stats['available loans'][self.month] = available_new_loans
        self.stats['loans held'][self.month] = len(self.investor.loans)
        self.stats['cumulative loans held'][self.month] = len(self.loans)
        self.stats['cumulative defaults'][self.month] = self.investor.cum_defaults
        self.stats['cash held'][self.month] = self.investor.balance
        self.stats['net worth'][self.month] = self.investor.get_net_worth()
        self.stats['imbalance'][self.month] = self.investor.cum_imbalance
        # self.stats['abs imbalance'][self.month] = self.investor.abs_cum_imbalance
        self.stats['imbalance %'][self.month] = self.stats['imbalance'][self.month] / self.stats['net worth'][self.month]
        # self.stats['abs imbalance %'][self.month] = self.stats['abs imbalance'][self.month] / self.stats['net worth'][self.month]
        
        #for key in self.statistics:
        #    print '    ', key, self.statistics[key][self.month]
        
        # print '    available contracts: ', purchase, 
        # print '    loans held: ', len(self.investor.loans) 
        # print '    cash held:  ', self.investor.balance
        # print '    net_worth:  ', self.investor.get_net_worth()
        # print '    imbalance:  ', self.investor.cum_imbalance
        self.month += 1
        
    def buy(self):
        month_db = self.db[self.db['issue_d'] == self.month]
        purchase_count = np.floor(self.investor.balance / self.buy_size)
        if purchase_count > 0:
            buy_df = self.buy_solver(self.month, self.investor, month_db, purchase_count)

            new_loans = buy_df.apply(self.map_loan_row, axis=1)
            # print new_loans

            self.investor.buy_loans(new_loans)
            return new_loans, month_db.shape[0]
        
        
    
    def map_loan_row(self, row):
        return Loan(
            loan_id=row['id'],
            grade=row['grade'],
            int_rate=row['int_rate'],
            term = row['term'],
            amount=row['funded_amnt'],
            issue_date=row['issue_d'],
            last_date=row['last_pymnt_d'],
            investment=self.buy_size,
            defaults=row['defaulted'],
            total_payment=row['total_pymnt'],
            total_principle=row['total_rec_prncp'],
            # recoveries=row['recoveries']
        )
        
    def run(self):
        while self.month <= self.end_month:
            print self.month, self.end_month
            self.solve_month()
            
        self.stats = pd.DataFrame(self.stats)
        self.stats['defaults'] = self.stats['cumulative defaults'].diff()
        self.stats['monthly return'] = self.stats['net worth'].diff().shift(-1) / self.stats['net worth']
        self.stats['annualized return'] = (self.stats['net worth'].resample('A').diff().shift(-1) / self.stats['net worth'].resample('A')).resample('M', fill_method='ffill')
        self.stats['growth of $1'] = self.stats['net worth'] / self.stats['net worth'].iloc[0]
        
        self.stats_dict = dict()
        self.stats_dict['sharpe'] = self.stats['net worth'].diff().mean() / self.stats['net worth'].diff().std() * np.sqrt(12)
        self.stats_dict = pd.Series(self.stats_dict)
            
        return self.stats
            
    
            