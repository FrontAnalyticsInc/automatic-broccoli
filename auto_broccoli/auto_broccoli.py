#!/usr/bin/env python
# -*- encoding: utf-8 -*-

"""http://faker.readthedocs.io/en/master/providers/faker.providers.address.html?highlight=random"""

import datetime as dt
import itertools
import random
import sys
from collections import defaultdict

import config
import numpy as np
import pandas as pd
import pandas_profiling as pp
from faker import Factory
from scipy import stats

from auto_broccoli import utils, database


class AutoBroccoli(object):
    """Designed for long data"""
    def __init__(self, df=None, categorical_as_ints=False, only_significant=False, sig_level=0.05, min_samples=30,
                 specific_config=None, table_name=None):
        self.dbi = database.DBInterface()
        if specific_config:
            self.running_config = specific_config
        else:
            self.running_config = config.IN_USE
        if table_name:
            self.table_name = table_name
        else:
            self.table_name = 'test'
        self.siglvl = sig_level
        self.min_samples = min_samples
        if categorical_as_ints:
            self.categorical_as_ints = True
        else:
            self.categorical_as_ints = False
        if only_significant:
            self.only_significant = True
        else:
            self.only_significant = False
        self.categorical_int_cutoff = 15
        if df is not None:
            self.df = pd.read_csv(df)
            self.dataset = 'custom'
        else:
            self.faker = Factory.create()
            self.df = pd.DataFrame([self.example_record() for _ in range(1000)])
            self.dataset = 'random'
        # self.granularity = self.intro()  #TODO: consider introducing this later
        self.run_date = dt.datetime.utcnow().strftime("%m-%d-%y")
        self.analysis_func_dict = {
            'bin X cat': self.bin_x_cat_insights,
            'bin X bin': self.bin_x_bin_insights,
            'bin X cont': self.bin_x_cont_insights,
            'cat X cont': self.cat_x_cont_insights,
            'cont X cont': self.cont_x_cont_insights
        }

    @staticmethod
    def intro():
        while True:
            try:
                granularity = input("Who/what are the actors in the dataset? (People, Stores, Clients, Patrons, etc): ")
            except ValueError:
                print("Sorry, I didn't get that: ")
                continue
            if not granularity:
                print("Sorry, can't be blank: ")
                continue
            elif granularity == 'stop':
                sys.exit()
            # elif approved not in ["Y", 'y', 'n', "N"]:
            #     print("Sorry, please select a 'Y' or a 'N'. To stop issue 'stop' : ")
            else:
                break
        # if approved in ["Y", 'y']:
        print(f"Analyzing on the granularity of {granularity}!")
        return granularity

    def date_between(self, d1, d2):
        f = '%b%d-%Y'
        return self.faker.date_time_between_dates(dt.datetime.strptime(d1, f), dt.datetime.strptime(d2, f))

    def example_record(self):
        """Generates a basic row of data for example data"""
        content_type = 'youtube,article,social media,doubleclick,newspaper'.split(',')
        return {'user_id': self.faker.ascii_email(),  # random user email
                'active': self.faker.boolean(),  # random status
                'nice_person': random.choice(['Y', 'N']),
                'buyer_type': random.choice(['me', 'spouse', 'friend', 'other']),
                'impressions': random.choice([1, 2, 3, 4, 5]),
                'content_type': random.choice(content_type),
                'visits': self.faker.random_number(3),
                'date': self.date_between('mar01-2018', 'apr01-2018'),
                'duration_percent':  1 - np.sqrt(1 - random.random())  # round(random.uniform(1, 100), 3)
                }

    def binary_checker(self, column):
        """Hackish way of negating the column name. For example, if the column were "active" and the values were False, True
        then we change the crosstab labels from False, True to "non-active" "active".

        Args:
            column: str, the name of the column that has a binary/boolean characteristic

        Returns:
            bool, str, str
        """
        unique_values = list(set(self.df[column].values))
        check1 = sum([isinstance(i, (bool, np.bool_)) for i in unique_values]) == 2
        check2 = all([isinstance(i, (int, np.uint8)) for i in unique_values]) and sum(unique_values) == 1
        if check1 or check2:
            return 'non-' + str(column), str(column)  # Hack negation of the column name
        else:
            raise ValueError(f'{column} not a binary variable? Unique values are : {unique_values}')

    def classify_column_types(self, ddf) -> dict:
        """One of the most important functions. This goes beyond Pandas Profiling to attempt to understand the
        analytical type of each column.

        Args:
            ddf: pandas Dataframe, pandas profiling description of data; equivalent of
                 pp.ProfileReport(df).get_description()['variables']
        Returns:
            dict, keys are analytical qualifiers (binary, continuous, etc) and values are lists of columns matching
        """
        _MEMO = defaultdict(list)

        for row in ddf.itertuples():

            tmp_df = self.df[self.df[row.Index].notnull()]
            values = tmp_df[row.Index].value_counts().index.tolist()
            value_counts = tmp_df[row.Index].value_counts().tolist()

            if row.type == 'UNIQUE':
                # TODO: what if continuous?
                _MEMO['unique identifier'].append(row.Index)

            elif row.type == 'DATE':
                # TODO: do a more robust date check for 20180106 and timestamps
                _MEMO['date'].append(row.Index)

            elif row.type == 'CONST':
                _MEMO['constant_value'].append(row.Index)

            elif row.type == 'CORR':
                _MEMO['highly_cross_correlated'].append(row.Index)

            elif row.type == 'NUM':
                if self.categorical_as_ints:
                    # Here we will see if numerical columns are actually categoricals
                    # NOTE: makes the assumption that at each category was selected at least once
                    if row.distinct_count < self.categorical_int_cutoff and utils.check_list_is_contiguous(values):
                        _MEMO['categorical'].append(row.Index)

                    elif row.distinct_count == 2 and len(value_counts) == 2:
                        # for bin X cat insist that there are at least 30 instances for each binary category
                        if min(value_counts) > 30:
                            _MEMO['binary'].append(row.Index)
                        # else:
                        #     _MEMO['possible_binary'].append(row.Index)
                    else:
                        _MEMO['continuous'].append(row.Index)
                else:
                    # Now any number should only represent a scalar
                    if row.is_unique and utils.id_column_check(row.Index):  # should match for any well labeled id column
                        _MEMO['unique identifier'].append(row.Index)

                    # elif row.is_unique and isinstance(ddf.loc[row.Index]['mode'], (float, int)):
                    #     _MEMO['continuous'].append(row.Index)

                    else:
                        _MEMO['continuous'].append(row.Index)

            elif row.type == 'CAT':
                if row.is_unique and isinstance(ddf.loc[row.Index]['mode'], str):
                    _MEMO['unique identifier'].append(row.Index)

                elif row.distinct_count > 25:
                    _MEMO['high_cardinality'].append(row.Index)

                elif row.distinct_count == 2 and len(value_counts) == 2:
                        # for bin X cat insist that there are at least 30 instances for each binary category
                        if min(value_counts) > 30:
                            self.df[row.Index] = pd.get_dummies(self.df[row.Index], drop_first=True)
                            _MEMO['binary'].append(row.Index)
                        # else:
                        #     _MEMO['possible_binary'].append(row.Index)
                elif len(value_counts) > 1 and min(value_counts) > 30:
                    _MEMO['categorical'].append(row.Index)

            elif row.type == 'BOOL':
                if min(value_counts) > 30:
                    _MEMO['binary'].append(row.Index)

            else:
                print(f'unknown case for {row.Index}')
                _MEMO['unknown case'].append(row.Index)

        return dict(_MEMO)

    @staticmethod
    def create_analytical_buckets(tcd):
        """ Creates a dictionary of columns to run thru tests on by type:
        # bin X bin:   chi-square test for difference, stats
        # bin X cat:   chi-square test for difference, stats
        # bin X cont:  T-test independent by group tests, stats
        # cont X cont:  correlations
        # cat X cont:  ANOVA
        Args:
            tcd: Type Columns Dict, a dict that holds the type as key and a list of columns as values

        Returns:
            results: dict, keys are the type of analysis
        """
        results = defaultdict(list)

        if 'binary' in tcd.keys() and 'categorical' in tcd.keys():
            # for chi-square tests
            for i in tcd['binary']:
                for j in tcd['categorical']:
                    results['bin X cat'].append([i, j])

        if 'binary' in tcd.keys() and 'continuous' in tcd.keys():
            # for t-tests
            for i in tcd['binary']:
                for j in tcd['continuous']:
                    results['bin X cont'].append([i, j])

        if 'categorical' in tcd.keys() and 'continuous' in tcd.keys():
            # for anovas
            for i in tcd['categorical']:
                for j in tcd['continuous']:
                    results['cat X cont'].append([i, j])

        if 'continuous' in tcd.keys() and len(tcd['continuous']) > 1:
            # for correlations
            unique_combos = list(itertools.combinations(tcd['continuous'], 2))
            for combo in unique_combos:
                results['cont X cont'].append(combo)

        if 'binary' in tcd.keys() and len(tcd['binary']) > 1:
            # for chi-square tests
            unique_combos = list(itertools.combinations(tcd['binary'], 2))
            for combo in unique_combos:
                results['bin X bin'].append(combo)

        return dict(results)

    # TODO: find a way to reduce repitition of code in the insights funcs below
    def bin_x_cat_insights(self, pair_list) -> (bool, dict):
        """Compares a binary column to a categorical column looking for insights

        Args:
            pair_list: list, contains the names of the columns to be compared

        Returns:
            dict of results for reporting
        """
        # Setup
        bin_var, cat_var = pair_list
        cat_unique_values = list(set(self.df[cat_var].values))
        bin_unique_values = list(set(self.df[bin_var].values))
        bin_label_1, bin_label_2 = self.binary_checker(bin_var)
        xtab = pd.crosstab(self.df[cat_var], self.df[bin_var])
        xtab.index = [i.title() for i in cat_unique_values]
        xtab.columns = bin_label_1, bin_label_2  # relabel so it's easier to work with

        # Analysis
        chi2, p, dof, expected = stats.chi2_contingency(xtab)
        insights = ""

        if p <= self.siglvl:
            insights += f"Significant difference in '{bin_label_1}' and '{bin_label_2}' between '{cat_var}' groups. "

        if (self.only_significant and insights) or not self.only_significant:
            insights += utils.crosstabs_on_binary_v_categorical(xtab, cat_var)
            # TODO: What to do about the magnitude?
            if insights:
                return True, {
                    'date': self.run_date, 'dataset': self.dataset, 'insight_text': insights, 'p_val': round(p, 4),
                    'magnitude': np.nan, 'col_1': bin_var, 'col_2': cat_var, 'analysis': 'Chi-square'
                }
            else:
                return False, {}
        else:
            return False, {}

    def bin_x_bin_insights(self, pair_list) -> (bool, dict):
        bin1_var, bin2_var = pair_list  # ['active', 'nice_person']
        bin1_unique_values = list(set(self.df[bin1_var].values))
        bin2_unique_values = list(set(self.df[bin2_var].values))
        bin_1_label_1, bin_1_label_2 = self.binary_checker(bin1_var, )
        bin_2_label_1, bin_2_label_2 = self.binary_checker(bin2_var, )
        dict_ = {'bin1var': bin1_var, 'bin2var': bin2_var,
                 'bin1_uniques': bin1_unique_values,
                 'bin2_uniques': bin2_unique_values,
                 'bin1_labels': [bin_1_label_1, bin_1_label_2],
                 'bin2_labels': [bin_2_label_1, bin_2_label_2]}
        xtab = pd.crosstab(self.df[dict_['bin1var']], self.df[dict_['bin2var']])
        xtabc = pd.crosstab(self.df[dict_['bin1var']], self.df[dict_['bin2var']], normalize='columns')
        xtabi = pd.crosstab(self.df[dict_['bin1var']], self.df[dict_['bin2var']], normalize='index')
        xtabc.index = dict_['bin1_labels']
        xtabc.columns = dict_['bin2_labels']
        fxtab = xtabi.T
        fxtab.index = dict_['bin2_labels']
        fxtab.columns = dict_['bin1_labels']

        # Analysis
        chi2, p, dof, expected = stats.chi2_contingency(xtab)
        insights = ""
        if p <= self.siglvl:
            insights += f"Significant difference in the '{bin_1_label_1}' and '{bin_1_label_2}' groups when " \
                        f"comparing to '{bin_2_label_1}' and '{bin_2_label_2}' groups. "
        if (self.only_significant and insights) or not self.only_significant:
            insights += utils.analyze_xtab_column_frequency(xtabc, dict_, label='bin2_labels')
            insights += utils.analyze_xtab_column_frequency(fxtab, dict_, label='bin1_labels')
            if insights:
                return True, {
                    'date': self.run_date, 'dataset': self.dataset, 'insight_text': insights, 'p_val': round(p, 4),
                    'magnitude': np.nan, 'col_1': bin1_var, 'col_2': bin2_var, 'analysis': 'Chi-square'
                }
            else:
                return False, {}
        else:
            return False, {}

    def bin_x_cont_insights(self, pair_list) -> (bool, dict):
        """Stuff"""
        bin_var, cont_var = pair_list
        # bin_unique_vals = list(set(self.df[bin_var].values))
        bin_label_1, bin_label_2 = self.binary_checker(bin_var)
        pos_desc = self.df[self.df[bin_var] == 1][cont_var].describe()
        neg_desc = self.df[self.df[bin_var] == 0][cont_var].describe()
        insights = ""
        t, p_val = stats.ttest_ind_from_stats(mean1=pos_desc['mean'], std1=pos_desc['std'], nobs1=pos_desc['count'],
                                              mean2=neg_desc['mean'], std2=neg_desc['std'], nobs2=neg_desc['count'])
        if p_val <= self.siglvl:
            insights += f'Significant difference in "{bin_label_1}" and "{bin_label_2}" in "{cont_var}". '

        if (self.only_significant and insights) or not self.only_significant:
            insights += utils.independent_t_test(bin_label_1, bin_label_2, cont_var, pos_desc, neg_desc)
            if insights:
                return True, {
                    'date': self.run_date, 'dataset': self.dataset, 'insight_text': insights, 'p_val': round(p_val, 4),
                    'magnitude': np.nan, 'col_1': bin_var, 'col_2': cont_var, 'analysis': 'T-test'
                }
            else:
                return False, {}
        else:
            return False, {}

    def cat_x_cont_insights(self, pair_list) -> (bool, dict):
        """Compares frequencies in a categorical column to a continuous variable

        Args:
            pair_list: list, contains the names of the columns to be compared

        Returns:
            dict of results for reporting
        """
        cat_var, cont_var = pair_list
        tmpdf = self.df[self.df[cat_var].notnull() & (self.df[cont_var].notnull())]  # Filter out nans
        insights = ""
        # Anova
        grps = pd.unique(tmpdf[cat_var].values)
        d_data = {grp: tmpdf[cont_var][tmpdf[cat_var] == grp] for grp in grps}
        f, p_val = stats.f_oneway(*d_data.values())

        if p_val <= self.siglvl:
            insights += f'Significant difference across groups in "{cat_var}" in "{cont_var}". '

        if (self.only_significant and insights) or not self.only_significant:
            insights += utils.cool_categories()
            if insights:
                return True, {
                    'date': self.run_date, 'dataset': self.dataset, 'insight_text': insights, 'p_val': round(p_val, 4),
                    'magnitude': np.nan, 'col_1': cat_var, 'col_2': cont_var, 'analysis': 'Anova'
                }
            else:
                return False, {}
        else:
            return False, {}

    def cont_x_cont_insights(self, pair_list) -> (bool, dict):
        """"""
        col_1, col_2 = pair_list
        coef, p_val = stats.pearsonr(self.df[col_1], self.df[col_2])

        if (self.only_significant and p_val <= self.siglvl) or not self.only_significant:
            insight_text = utils.correlations(coef, p_val, self.siglvl, col_1=col_1, col_2=col_2)
            if insight_text:
                return True, {
                    'date': self.run_date, 'dataset': self.dataset, 'insight_text': insight_text,
                    'p_val': round(p_val, 4), 'magnitude': np.nan, 'col_1': col_1, 'col_2': col_2,
                    'analysis': 'Pearson corr'
                }
            else:
                return False, {}
        else:
            return False, {}

    def auto_analysis(self, d_) -> pd.DataFrame:
        """Goes thru the available analytical combinations and writes out to a dataframe any findings found

        Args:
            d_: dict, the analytical combinations dict

        Returns:
            results_df, pandas DataFrame of findings
        """
        results = []
        for k, v in d_.items():
            func = self.analysis_func_dict.get(k)
            if func:
                for i in v:
                    success, result = func(i)
                    if success:
                        result['analysis_type'] = k
                        results.append(result)
        results_df = pd.DataFrame(results)
        return results_df

    def main(self):

        # Step 1: run the awesome pandas profiling
        pobject = pp.ProfileReport(self.df)
        des = pobject.get_description()

        # Step 2: identify analytical types of variables
        analytics_df = des['variables']
        type_dict = self.classify_column_types(analytics_df)

        # Step three: set them into analytical buckets
        analytics_dict = self.create_analytical_buckets(type_dict)

        # Step four: run the analytics!
        _df = self.auto_analysis(d_=analytics_dict)
        if self.running_config.WRITE_TO_DB:
            self.dbi.save_to_table(_df, table_name=self.table_name, replace_or_append=self.running_config.DB_WRITE_MODE)
            print(f'Saved results to table {self.table_name}.')
        return _df


if __name__ == '__main__':
    ai = AutoBroccoli()
    df = ai.main()
    print(df)
