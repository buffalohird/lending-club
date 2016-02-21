from loan import Loan

class Investor():
    def __init__(self, balance=1000, loans=None):
        self.loans = loans or list()
        self.balance = balance
        self.cum_imbalance = 0
        self.cum_defaults = 0
        self.abs_cum_imbalance = 0
    
    def get_net_worth(self):
        return self.balance + sum([loan.get_pv() for loan in self.loans])
    
    def get_payments(self):
        for loan in self.loans:
            received = loan.make_payment()
            self.balance += received
            if loan.complete:
                self.cum_defaults += loan.defaults
                self.cum_imbalance += loan.get_imbalance()
                # self.abs_cum_imbalance += loan.get_abs_imbalance()
                self.remove_loan(loan)
                
    def buy_loans(self, loans):
        for loan in loans:
            self.add_loan(loan)
            self.balance -= loan.investment
        
    def add_loan(self, loan):
        if loan not in self.loans:
            self.loans.append(loan)
            
                
    def remove_loan(self, loan):
        if loan in self.loans:
            self.loans.remove(loan)
             