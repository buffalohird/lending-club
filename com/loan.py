import numpy as np

class Loan():
    def __init__(self, loan_id, grade, int_rate, term, amount, issue_date, 
                 last_date, defaults, investment, total_payment, total_principle, recoveries):
        self.id = loan_id
        self.grade = grade
        self.int_rate = int_rate
        self.term = int(term.strip().split(' ')[0])
        self.amount = amount
        self.initial_amount = self.amount
        
        self.issue_date = issue_date
        self.last_date = last_date
        self.investment = investment
        self.defaults = defaults
        self.total_payment = total_payment
        self.total_principle = total_principle
        self.recoveries = recoveries
        self.imbalance_ratio = np.nan
        
        
        self.term_realized = self.last_date - self.issue_date
        if self.defaults:
            # warnings.warn('have not yet implemented defaulting loans')
            self.amount = self.total_payment
            
        
        self.installment = np.round(-np.pmt(self.int_rate / 12, self.term_realized, self.amount), 2)
        self.remaining_term = self.term_realized
        
        self.scale = (self.investment / self.initial_amount)
        
        self.imbalance = 0
        self.complete = False
        self.fee = 0.01

    def to_dict(self):
        return {
            'id': self.id,
            'grade': self.grade,
            'int_rate': self.int_rate,
            'amount': self.initial_amount,
            'term': self.term,
            'remaining_amount': self.get_pv(),
            'issue_date': self.issue_date,
            'end_date': self.last_date,
            'investment': self.investment,
            'defaulted': self.defaults,
            'absolute_imbalance': self.get_abs_imbalance(),
            'installment': self.installment * self.scale,
            'imbalance': self.get_imbalance(),
            'completed': self.complete,
            'imbalance_percentage': self.imbalance_ratio,
            'remaining_terms': self.remaining_term,
            'fee': self.fee,
        }
        
    def get_pv(self):
        # get present value
        if self.defaults:
            # i.e. the perceived value is the amount to be paid + the additional principle we fail to receive
            return (self.amount + self.initial_amount - self.total_payment) * self.scale
        return self.amount * self.scale
        
    def make_payment(self):
        payment_made = min(self.installment, self.amount)
        payment_interest = self.int_rate / 12 * self.amount
        payment_principal = payment_made - payment_interest
        self.amount -= payment_principal
        self.remaining_term -= 1
        
        payment_received = payment_made * (1.0 - self.fee)
        self.imbalance += payment_received
        self.check_completion()
        return payment_received * self.scale
    
    def get_imbalance(self):
        return self.imbalance * self.scale

    def get_abs_imbalance(self):
        return abs(self.imbalance) * self.scale
    
    def check_completion(self):
        if self.remaining_term == 0:
            self.imbalance -= self.total_payment * (1.0 - self.fee)
            self.imbalance_ratio = self.imbalance / self.total_payment
            # print self.imbalance_ratio, self.defaults
            self.complete = True



