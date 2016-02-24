from jinja2 import Template, Environment, PackageLoader
from collections import OrderedDict


class Report():

    def __init__(self, backtest, filepath=None):
        self.backtest = backtest
        self.filepath = filepath

    def save(self, filepath=None):
        if not filepath:
            filepath = self.filepath

        bt = self.backtest
        
        summary_dict = OrderedDict()
        summary_dict['Title'] = 'Lending Club Report'
        summary_dict['Date'] = str(datetime.datetime.now()).split('.')[0]
        summary_dict['Solver Function'] = bt.buy_solver_name
        summary_dict['Annualized Return'] = np.round((1.0 + bt.stats['monthly return']['20120101':].mean()) ** 12, 3)
        summary_dict['Annualized Volatity'] = np.round(bt.stats['monthly return'].std() * np.sqrt(12), 3)
        summary_dict['Mean Return'] = np.round(bt.stats['monthly return'].mean(), 3)
        summary_dict['Standard Deviation'] = np.round(bt.stats['monthly return'].std(), 3)
        summary_dict['Skew'] = np.round(bt.stats['monthly return'].skew(), 3)
        summary_dict['Kurtosis'] = np.round(bt.stats['monthly return'].kurt(), 3)
        summary_dict['Sharpe'] = np.round(bt.stats_dict['sharpe'], 3)
        summary_dict['Transaction Fee'] = 0.01
        
        summary_df = pd.Series(summary_dict)
        
        net_worth = bt.stats['net worth'].plot(title='Net Worth', figsize=(18,8))
        net_worth.get_figure().savefig('net_worth.png')
        plt.close()    
        
        monthly_return = bt.stats['monthly return'].plot(title='Monthly Returns', figsize=(6,8))
        monthly_return.get_figure().savefig('monthly_return.png')
        plt.close()
        
        mean_duration = bt.loan_stats['duration'].mean(axis=1).plot(title='Mean Portfolio Remaning Lifetime', figsize=(6,8))
        mean_duration.get_figure().savefig('mean_duration.png')
        plt.close()
        
        default_rate = bt.stats['default rate'].plot(title='Default Rate', figsize=(6,8))
        default_rate.get_figure().savefig('default_rate.png')
        plt.close()

        growth_of_one = bt.stats['growth of $1'].plot(title='Growth of $1', )
        growth_of_one.get_figure().savefig('growth_of_one.png')
        plt.close()
        
        int_rate_breakdown = bt.loan_stats_total['int_rate'].plot.hist(title='Distribution of Interest Rates', figsize=(6,8))
        int_rate_breakdown.get_figure().savefig('int_rate_breakdown.png')
        plt.close()

        grade_breakdown = (bt.loan_stats_total['grade'] / bt.loan_stats_total['grade'].sum()).plot.bar(title='Distribution of Grades', figsize=(6,8), colors='rgbymc')
        grade_breakdown.get_figure().savefig('grade_breakdown.png')
        plt.close()
        
        imbalance_percentage = bt.loan_stats_total['imbalance_percentage'][bt.loan_stats_total['imbalance_percentage'].abs() <= 0.1].plot.hist(figsize=(6,8), title='Distribution of Loan Imbalance', bins=30)
        imbalance_percentage.get_figure().savefig('imbalance_percentage.png')
        plt.close()
        
        available_loans = bt.stats['available loans'].plot(title='Available Loans', figsize=(6, 8))
        available_loans.get_figure().savefig('available_loans.png')
        plt.close()  
        
        
        loans_held = bt.stats['loans held'].plot(label='Loans Held', title='Loans Held', figsize=(6,8))
        bt.stats['loans added'].plot(label='Loans Added', title='Loans Added', figsize=(6, 8))
        plt.legend()
        loans_held.get_figure().savefig('loans_held.png')
        plt.close()
        
        cash_held = bt.stats['cash held'].plot(title='Cash Held', figsize=(6,8))
        cash_held.get_figure().savefig('cash_held.png')
        plt.close()
        
        liquidity = bt.stats['total liquidity'].plot(title='Liquidity (% Market Cap)', label='Total Liquidity', figsize=(6, 8))
        bt.stats['strategy liquidity'].plot(label='Strategy Liquidity', figsize=(6, 8))
        plt.legend()
        liquidity.get_figure().savefig('liquidity.png')
        plt.close()
        
        
        grade_monthly = (bt.loan_stats['grade']).plot(title='Monthly Breakdown by Grade', figsize=(10,8))
        grade_monthly.get_figure().savefig('grade_monthly.png')
        plt.close()
        
        grade_int_monthly = bt.loan_stats['grade_int_rate'].plot(title='Monthly Interest Rate by Grade', figsize=(10,8))
        grade_int_monthly.get_figure().savefig('grade_int_monthly.png')
        plt.close()
            
        env = Environment(loader=PackageLoader('reports', 'templates'))
        template = env.get_template('template.html')
        css = env.get_template('report.css')
        
        output = template.render(
            css=css.render(),
            summary = pd.DataFrame(summary_df).to_html()
        )
        
        with open(filepath, 'w') as fp:
            fp.write(output)
        return output