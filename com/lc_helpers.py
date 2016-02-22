import datetime

import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt


def get_db_folder():
  downloads = '/Users/thegator12321/Downloads/'
  db_dict = {
    'training': '{}{}'.format(downloads, 'LoanStats3a.csv'),
    'testing': '{}{}'.format(downloads, 'LoanStats3b.csv')
  }
  return db_dict


def df_ols(df, y, x):
    for var in [x, y]:
        if not hasattr(var, '__iter__'):
            var = [var]
    return pd.ols(y=df[y], x=df[x])


def make_df_numeric(df, remove_nans=False):
    
    fixed_df = df.pipe(create_relevant_subset).pipe(create_factors, return_components=False)
    if remove_nans:
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
    states = states_dummies.columns
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
      return short_df, purposes, states
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
    
    for column in ['mths_since_last_delinq', 'mths_since_last_record',]:#'mths_since_last_major_derog']:
        short_df[column] = short_df[column].fillna(short_df[column].max())
    
    return short_df
