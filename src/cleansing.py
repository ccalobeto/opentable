# Program by Carlos León

import pandas as pd
import subprocess
import numpy as np
from itertools import chain

'''
Data obtained from
https://www.opentable.com/state-of-industry
'''

""" DESIGN SCHEMA """
# LOCAL FUNCTIONS
# GLOBAL VARIABLES
# IMPORT
# PREPARE
#  Clean
#  Transform
#   convert pivot to transactional data
#   modify values
#  Join
#   initial joins
#   create special features
#   final joins
# EXPORT

# LOCAL FUNCTIONS
# return list from series of comma-separated strings


def chainer(s):
    ''' returns a list of state codes '''
    return list(chain.from_iterable(s.str.split(',')))

# GLOBAL VARIABLES


DECIMAL_DIGITS = 2
NUMBER_TOP_DATES = 3
DATE_MIN_STR = '2020-03-31'
INPUT_PATH = '../input/'
OUTPUT_PATH = '../output/'

FILE_1_ = 'YoY_Seated_Diner_Data.csv'
FILE_2_ = 'holidays.xlsx'
FILE_3_ = 'states.xlsx'

# IMPORT DATA
print('IMPORTING DATA...')
openings_df_ = pd.read_csv(INPUT_PATH + FILE_1_)
holidays_df_ = pd.read_excel(INPUT_PATH + FILE_2_, sheet_name='holidays')
stateCodes_df_ = pd.read_excel(INPUT_PATH + FILE_3_)

print(f' File Imported from: {INPUT_PATH + FILE_1_}')
print(f' File Imported from: {FILE_2_}')
print(f' File Imported from: {INPUT_PATH + FILE_3_}')


# PREPARE DATA
#  Clean data
#   filter relevant data
openings_df_.rename(columns={'Type': 'typeOflocality', 'Name': 'locality'}, inplace=True)
holidays_df_.rename(columns={'Date': 'date_', 'Name': 'holidayName', 'Type': 'typeOfHoliday',
                             'Details': 'details', 'Country': 'country'}, inplace=True)
stateCodes_df_.rename(columns={'abbreviation': 'stateCode'}, inplace=True)

openings_df_ = openings_df_[openings_df_['locality'] != 'Global'].reset_index(drop=True)
openings_df_ = openings_df_[openings_df_['typeOflocality'] != 'city'].reset_index(drop=True)
openings_df_['locality'] = openings_df_['locality'].replace({'Rhineland-Palatinate': 'Rheinland-Pfalz',
                                                             'District of Columbia': 'District Of Columbia'})
openings_df_.drop(labels=['typeOflocality'], inplace=True, axis=1)
openings_df_.dropna(inplace=True)

stateCodes_df_['state'] = stateCodes_df_['state'].str.title()
stateCodes_df_['state'] = stateCodes_df_['state'].replace({'Districto Federal': 'Mexico City'})

holidays_df_['details'].fillna('All States', inplace=True)
allCharacterIndices = holidays_df_[holidays_df_['details'].str.contains('All')].index.values
holidays_df_.loc[allCharacterIndices, 'details'] = 'All States'
holidays_df_[['day', 'remove_col', 'month']] = holidays_df_['date_'].str.split(expand=True)
months = {'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4, 'may': 5, 'jun': 6, 'jul': 7, 'ago': 8, 'sep': 9, 'oct': 10,
          'nov': 11, 'dic': 12}
holidays_df_['date'] = pd.to_datetime({'year': [2020] * holidays_df_.shape[0],
                                       'month': holidays_df_['month'].map(months),
                                       'day': holidays_df_['day']})
holidays_df_['weekOfYear'] = holidays_df_['date'].dt.weekofyear
holidays_df_.drop(labels=['date_', 'Day', 'day', 'remove_col', 'month'], inplace=True, axis=1)

#  Transform data
#   convert pivot to transactional data
openings_df = openings_df_.set_index('locality').stack().reset_index()
openings_df.rename(columns={'level_1': 'date_', 0: 'openingRate'}, inplace=True)
openings_df[['month', 'day']] = openings_df['date_'].str.split('/', expand=True)
openings_df['date'] = pd.to_datetime({'year': [2020] * openings_df.shape[0],
                                      'month': openings_df['month'],
                                      'day': openings_df['day']})

#   create common variables
openings_df.loc[:, 'weekOfYear'] = openings_df['date'].dt.weekofyear
openings_df['isDateAfterMarch'] = 'No'
#    a boolean variable if date if after March
openings_df.loc[openings_df[openings_df['date'] > DATE_MIN_STR].index.values, 'isDateAfterMarch'] = 'Yes'
openings_df.drop(labels=['date_', 'month', 'day'], inplace=True, axis=1)

#   convert pivot to transactional data
#    calculate lengths of splits
numberOfStates = holidays_df_['details'].str.split(',').map(len)
#    create new dataframe, repeating or chaining as appropriate
holidays_df = pd.DataFrame({'holidayName': np.repeat(holidays_df_['holidayName'], numberOfStates),
                            'typeOfHoliday': np.repeat(holidays_df_['typeOfHoliday'], numberOfStates),
                            'details': np.repeat(holidays_df_['details'], numberOfStates),
                            'country': np.repeat(holidays_df_['country'], numberOfStates),
                            'date': np.repeat(holidays_df_['date'], numberOfStates),
                            'weekOfYear': np.repeat(holidays_df_['weekOfYear'], numberOfStates),
                            'locality': chainer(holidays_df_['details'])})
holidays_df = holidays_df.reset_index(drop=True)

#   remove values and modify values
holidays_df['locality'] = holidays_df['locality'].str.strip('*')
holidays_df['locality'] = holidays_df['locality'].str.strip()
holidays_df['locality'] = holidays_df['locality'].replace({'Qld': 'QLD', 'NL': 'NF', 'NRW': 'NW',
                                                           'MVP': 'MV', 'RLP': 'RP', 'NDS': 'NI',
                                                           'Vic': 'VIC'})

#  Join Tables
#   initial joins
holidays_df = holidays_df.merge(stateCodes_df_, how='left', left_on=['locality', 'country'],
                                                right_on=['stateCode', 'country'])

openings_df = openings_df.merge(stateCodes_df_[['state', 'country']], left_on='locality', right_on='state', how='left')
openings_df['country'] = openings_df['country'].fillna(openings_df['locality'])

#   create special features
#    a boolean variable, detect if the date is over a top date sell
topRateIndices = openings_df[openings_df['openingRate'] > 0].sort_values(['country', 'state', 'openingRate'],
                                                                               ascending=False).\
    groupby(['country', 'state']).head(NUMBER_TOP_DATES).index.values
openings_df['isRateOverLastYear'] = 'No'
openings_df.loc[topRateIndices, 'isRateOverLastYear'] = 'Yes'
#    locality position variable
# openings_df['cumulativePositiveRate'] = openings_df['openingRate'].apply(lambda x: 0 if x < 0 else x)
openings_df['cumulativePositiveRate'] = openings_df.groupby('locality')['openingRate'].transform('sum')
cumulativePositiveRates_df = openings_df[['country', 'locality', 'cumulativePositiveRate']].drop_duplicates().\
    sort_values(['country', 'cumulativePositiveRate'], ascending=False).reset_index(drop=True)
cumulativePositiveRates_df['localityPosition'] = cumulativePositiveRates_df.groupby('country')['cumulativePositiveRate'].\
    cumcount()
openings_df = openings_df.merge(cumulativePositiveRates_df[['locality', 'localityPosition']],
                                on='locality', how='left')

#    adjusting locality variable for conditional merging
localities_lst = openings_df['locality'].drop_duplicates().to_list()
stateConvertedIndices = holidays_df[holidays_df['state'].notnull()].index.values
countryIndices = holidays_df[(holidays_df['state'].isnull()) & (holidays_df['locality'] == 'All States')].index.values
nonIdentifiedLocalities = holidays_df[(holidays_df['state'].isnull()) & (~holidays_df['locality'].
                                                                         isin(localities_lst))].index.values
holidays_df.loc[stateConvertedIndices, 'locality'] = holidays_df.loc[stateConvertedIndices]['state']
holidays_df.loc[countryIndices, 'locality'] = holidays_df.loc[countryIndices]['country']
holidays_df.loc[nonIdentifiedLocalities, 'locality'] = holidays_df.loc[nonIdentifiedLocalities]['country']
holidays_df.drop(labels=['state', 'stateCode', 'country'], inplace=True, axis=1)

#    final joins
#     merge into two conditional keys: date and locality
cleanedOpenings_df = openings_df.merge(holidays_df[['holidayName', 'date', 'locality']].
                                      drop_duplicates(subset=['date', 'locality']), how='left', on=['date', 'locality'])

cleanedOpenings_df.drop(labels=['state'], inplace=True, axis=1)

# EXPORT DATA
cutOffDateStr = max(openings_df['date']).strftime("%Y-%m-%d")
file_1 = cutOffDateStr + '_' + FILE_1_.split('.')[0] + '_Cleaned.csv'
file_2 = FILE_2_.split('.')[0] + '_Cleaned.csv'
cleanedOpenings_df.to_csv(OUTPUT_PATH + file_1, index=False)
holidays_df.to_csv(OUTPUT_PATH + file_2, index=False)

print()
print('EXPORTING DATA...')
print(f' File Exported: {OUTPUT_PATH + file_1}')
print(f' File Exported: {OUTPUT_PATH + file_2}')
subprocess.call(['afplay', '../sounds/Water Bowl 09A.wav'])
