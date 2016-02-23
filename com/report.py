from backtest import Backtest

class Report():

  def __init__(self, backtest, filepath=None):
    self.backtest = backtest
    self.filepath = filepath

  def save(self, filepath):
    if not filepath:
      filepath = self.filepath