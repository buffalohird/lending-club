import datetime
import os
import warnings

import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt


states = ['state_MT', 'state_NE', 'state_NV', 'state_NH', 'state_NJ',
          'state_NM', 'state_NY', 'state_NC', 'state_ND', 'state_OH',
          'state_OK', 'state_OR', 'state_PA', 'state_RI', 'state_SC',
          'state_SD', 'state_TN', 'state_TX', 'state_UT', 'state_VT',
          'state_VA', 'state_WA', 'state_WV', 'state_WI', 'state_WY',
          'state_AL', 'state_AK', 'state_AZ', 'state_AR', 'state_CA',
          'state_CO', 'state_CT', 'state_DE', 'state_FL', 'state_GA',
          'state_HI', 'state_ID', 'state_IL', 'state_IN', 'state_IA',
          'state_KS', 'state_KY', 'state_LA', 'state_ME', 'state_MD',
          'state_MA', 'state_MI', 'state_MN', 'state_MS', 'state_MO']

purposes = ['purpose_car', 'purpose_credit_card', 'purpose_debt_consolidation',
            'purpose_educational', 'purpose_home_improvement', 'purpose_house',
            'purpose_major_purchase', 'purpose_medical', 'purpose_moving',
            'purpose_other', 'purpose_renewable_energy',
            'purpose_small_business', 'purpose_vacation', 'purpose_wedding']

def get_db_folder():
  data_folder = '../data/'
  db_dict = {
    'training': '{}{}'.format(downloads, 'LoanStats3a.csv'),
    'testing': '{}{}'.format(downloads, 'LoanStats3b.csv'),
    'testing2': '{}{}'.format(downloads, 'LoanStats3c.csv'),
    'testing3': '{}{}'.format(downloads, 'LoanStats3d.csv'),
    'complete': '{}{}'.format(downloads, 'LoanStatsTotal.csv'),
    'cache': '{}{}'.format(downloads, 'loan_cache.hdf5')
  }
  return db_dict

def get_cache_historic(rewrite=False):
    db = get_db_folder()
    cache_file = db['cache']
    if os.path.exists(cache_file) and not rewrite:
        return pd.read_hdf(cache_file, 'historic')
    else:
        warnings.warn('Historic Cache does not exist, creating at {cache_file}'.format(cache_file=cache_file))
        training = pd.read_csv(db['training']).pipe(make_df_numeric, fix_nans=True)
        testing = pd.read_csv(db['testing']).pipe(make_df_numeric, fix_nans=True)
        testing2 = pd.read_csv(db['testing2']).pipe(make_df_numeric, fix_nans=True)
        testing3 = pd.read_csv(db['testing3']).pipe(make_df_numeric, fix_nans=True)
        historic_df = pd.concat([training, testing, testing2, testing3])
        historic_df.to_hdf(cache_file, 'historic')



def df_ols(df, y, x):
    for var in [x, y]:
        if not hasattr(var, '__iter__'):
            var = [var]
    return pd.ols(y=df[y], x=df[x])


def make_df_numeric(df, edate='20170101', fix_nans=False):

    fixed_df = df.pipe(create_relevant_subset, edate=edate).pipe(create_factors, return_components=False)
    if fix_nans:
      return fixed_df.pipe(remove_nans)
    return fixed_df


def fix_issue_date(x):
    try:
        return pd.Period(datetime.datetime.strptime(str(x), '%b-%y'), 'M')
    except:
        return None


def create_relevant_subset(df, grades=['A','B','C','D','E','F','G'], edate='20130101'):
    df['loan_status'] = df['loan_status'].str.replace('Does not meet the credit policy. Status:', '')
    df = df.iloc[df['loan_status'].isin(['Fully Paid', 'Charged Off']).index, :].reset_index(drop=True)
    df = df[df['term'] == ' 36 months']
    df = df[df['grade'].isin(grades)]
    df['issue_d'] = df['issue_d'].map(fix_issue_date).reindex()
    df = df[df['issue_d'] < pd.Period(edate, freq='M')]
    return df


def create_factors(short_df, return_components=True):
    # create y variables
    short_df['defaulted'] = short_df['loan_status'].isin(['Charged Off']).astype(int)

    short_df['profit'] = short_df['total_pymnt'] / short_df['funded_amnt']
    short_df['annualized_profit'] = short_df['profit'] ** (1.0/3.0)
    short_df['annualized_ten_percent'] = short_df['annualized_profit']


    # create x variables
    short_df['verified'] = (~short_df['verification_status'].str.lower().str.contains('not')).astype(int)

    purpose_dummies = pd.get_dummies(short_df['purpose'])
    purpose_dummies.columns = ['purpose_' + column for column in purpose_dummies.columns]
    purposes = purpose_dummies.columns
    for purpose in purposes:
        purpose_dummies[purpose] = purpose_dummies[purpose].astype(float)
    short_df = pd.concat([short_df, purpose_dummies], axis=1)

    short_df['own_home'] = short_df['home_ownership'].isin(['MORTGAGE', 'OWN'])
    short_df['joint_account'] = short_df['application_type'].isin(['JOINT'])

    states_dummies = pd.get_dummies(short_df['addr_state'])
    states_dummies.columns = ['state_' + column for column in states_dummies.columns]
    for state in states:
        if state not in states_dummies.columns:
            states_dummies[state] = 0 # if state not there, dummy=0 for all rows
    short_df = pd.concat([short_df, states_dummies], axis=1)

    latest = short_df['earliest_cr_line'].map(fix_issue_date).reindex()
    short_df['credit_history'] = np.maximum((short_df['issue_d'] - latest), 1)

    short_df['last_pymnt_d'] = short_df['last_pymnt_d'].map(fix_issue_date).reindex()
    short_df = short_df[~short_df['last_pymnt_d'].isnull()]

    import string
    short_df['grade_int'] = short_df['grade'].apply(lambda x: string.lowercase.index(x.lower()))

    short_df['dti'] = short_df['dti'] / 100

    for column in ['int_rate', 'revol_util']:
        short_df[column] = short_df[column].str.replace('%', '').astype(float) / 100

    short_df['emp_length'] = short_df['emp_length'].str.replace('n/a', '0').str.replace('<', '0').str.replace('+', '').str.split(' ').str[0]

    for column in ['id', 'member_id', 'loan_amnt', 'dti', 'mths_since_last_delinq', 'mths_since_last_record', 'revol_bal',
               'revol_util', 'annual_inc', 'open_acc', 'total_acc', 'credit_history', 'emp_length', 'own_home',
               'pub_rec', 'installment', 'mths_since_last_major_derog', 'joint_account', 'recoveries', 'total_rec_prncp'
               ,'total_pymnt']:
        short_df[column] = short_df[column].astype(float)

    for column in ['loan_status']:
        short_df[column] = short_df[column].astype(str)
    if return_components:
      return short_df
    return short_df


def remove_nans(short_df):
    # fill nans
    short_df['inq_last_6mths'] = short_df['inq_last_6mths'].fillna(0)
    short_df['delinq_2yrs'] = short_df['delinq_2yrs'].fillna(0)

    short_df['pub_rec'] = short_df['pub_rec'].fillna(0)
    short_df['total_acc'] = short_df['total_acc'].fillna(0)
    short_df['annual_inc'] = short_df['annual_inc'].fillna(short_df['annual_inc'].mean())
    short_df['open_acc'] = short_df['open_acc'].fillna(short_df['open_acc'].mean())
    short_df['revol_util'] = short_df['revol_util'].fillna(short_df['revol_util'].median())

    for purpose in purposes:
        if purpose not in short_df.columns:
            short_df[purpose] = 0

    for column in ['mths_since_last_delinq', 'mths_since_last_record',]:#'mths_since_last_major_derog']:
        short_df[column] = short_df[column].fillna(short_df[column].max())
    return short_df
