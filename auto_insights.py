#!/usr/bin/env python
# -*- encoding: utf-8 -*-

"""http://faker.readthedocs.io/en/master/providers/faker.providers.address.html?highlight=random"""

import pandas_profiling as pp
import pandas as pd
import numpy as np
from faker import Factory
from datetime import datetime
import random
from scipy import stats
import re
import sys
from collections import defaultdict
import itertools
from src.inflect import inflect
import speak_easy


class AutoInsightsLong(object):
    """Designed for long data"""
    def __init__(self, df=None, dataset=None, categorical_as_ints=False, only_significant=False, sig_level=0.05, min_samples=30):
        self.S = inflect.engine()
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
        self.faker = Factory.create()
        # self.content_piece = 'video,article,social_media'.split(',')
        self.cat_ordinal = [1, 2, 3, 4, 5]
        if df is not None:
            self.df = df
            self.dataset = dataset
        else:
            self.df = pd.DataFrame([self.example_record() for _ in range(1000)])
            self.dataset = 'random'
        self.granularity = self.intro()
        self.run_date = str(datetime.now())

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
        return self.faker.date_time_between_dates(datetime.strptime(d1, f), datetime.strptime(d2, f))

    def example_record(self):
        content_type = 'youtube,article,social media,doubleclick,newspaper'.split(',')
        return {'user_id': self.faker.ascii_email(),  # random user email
                'active': self.faker.boolean(),  # random status
                'nice_person': random.choice(['Y', 'N']),
                'buyer_type': random.choice(['me', 'spouse', 'friend', 'other']),
                'some_category': random.choice(self.cat_ordinal),
                'content_type': random.choice(content_type),
                'visits': self.faker.random_number(3),  # id's eg:1,20,28,27
                'date': self.date_between('mar01-2018', 'apr01-2018'),  # datetime between mar01-2015 to mar15-2015
                'duration_percent': round(random.uniform(1, 100), 3)  # watch duration perc, 1 - np.sqrt(1 - random.random()) #
                }

    @staticmethod
    def id_column_check(string):
        """Takes in a column and returns a check to see if it thinks it's an identifier column"""
        success = re.match(r'\w*ID|\w*Id|\w*_ID|\w*_Id|\w*_id|account', string, re.IGNORECASE)
        if success:
            return True
        else:
            return False

    @staticmethod
    def check_list_is_contiguous(list_of_ints) -> bool:
        """Checks that a list of ints is contiguous
        https://stackoverflow.com/questions/28885455/python-check-whether-list-is-sequential-or-not
        """
        sorted_list = sorted(list_of_ints)
        it = (x for x in sorted_list)
        first = next(it)
        return all(a == b for a, b in enumerate(it, first + 1))

    def check_for_categorical(self, ddf):
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
                    if row.distinct_count < self.categorical_int_cutoff and self.check_list_is_contiguous(values):
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
                    if row.is_unique and self.id_column_check(row.Index):  # should match for any well labeled id column
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

    def bin_x_cat_insights(self, pair_list, type_) -> (bool, dict):
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
        success, bin_label_1, bin_label_2 = speak_easy.binary_checker(bin_var, bin_unique_values)
        xtab = pd.crosstab(self.df[cat_var], self.df[bin_var])

        if type_ == "bin X bin":
            success, cat_label_1, cat_label_2 = speak_easy.binary_checker(cat_var, cat_unique_values)
            xtab.index = [cat_label_1, cat_label_2]
        else:
            xtab.index = [i.title() for i in cat_unique_values]

        if success:
            xtab.columns = bin_label_1, bin_label_2  # relabel so it's easier to work with
        else:
            xtab.columns = bin_unique_values

        # Analysis
        chi2, p, dof, expected = stats.chi2_contingency(xtab)
        insights = ""

        if p <= self.siglvl:
            insights += f"Significant difference in {bin_label_1} and {bin_label_2} between {cat_var} groups. "

        if (self.only_significant and insights) or not self.only_significant:
            insights += speak_easy.cool_crosstabs(xtab, cat_var)
            # TODO: What to do about the magnitude?
            if insights:
                return True, {
                    'date': self.run_date, 'dataset': self.dataset, 'insight_text': insights, 'p_val': round(p, 4),
                    'magnitude': np.nan, 'col_1': bin_var, 'col_2': cat_var,
                }
            else:
                return False, {}
        else:
            return False, {}

    def bin_x_cont_insights(self, pair_list) -> (bool, dict):
        """Stuff"""
        bin_var, cont_var = pair_list
        bin_unique_values = list(set(self.df[bin_var].values))
        success, bin_label_1, bin_label_2 = speak_easy.binary_checker(bin_var, bin_unique_values)
        pos_desc = self.df[self.df[bin_var] == 1][cont_var].describe()
        neg_desc = self.df[self.df[bin_var] == 0][cont_var].describe()
        insights = ""
        t, p_val = stats.ttest_ind_from_stats(mean1=pos_desc['mean'], std1=pos_desc['std'], nobs1=pos_desc['count'],
                                              mean2=neg_desc['mean'], std2=neg_desc['std'], nobs2=neg_desc['count'])
        if p_val <= self.siglvl:
            insights += f"Significant difference in {bin_label_1} and {bin_label_2} in {cont_var}. "

        if (self.only_significant and insights) or not self.only_significant:
            insights += speak_easy.tight_t_test(bin_var, cont_var, bin_unique_values, pos_desc, neg_desc)
            if insights:
                return True, {
                    'date': self.run_date, 'dataset': self.dataset, 'insight_text': insights, 'p_val': round(p_val, 4),
                    'magnitude': np.nan, 'col_1': bin_var, 'col_2': cont_var,
                }
            else:
                return False, {}
        else:
            return False, {}

    def cat_x_cont_insights(self, pair_list):
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
            insights += f"Significant difference across groups in {cat_var} in {cont_var}. "

        if (self.only_significant and insights) or not self.only_significant:
            insights += speak_easy.cool_categories()
            if insights:
                return True, {
                    'date': self.run_date, 'dataset': self.dataset, 'insight_text': insights, 'p_val': round(p_val, 4),
                    'magnitude': np.nan, 'col_1': cat_var, 'col_2': cont_var,
                }
            else:
                return False, {}
        else:
            return False, {}

    def auto_analysis(self, d_) -> pd.DataFrame:
        """"""
        results = []
        for k, v in d_.items():
            if k == 'bin X cat' or k == 'bin X bin':
                for i in v:
                    success, bin_cat_results = self.bin_x_cat_insights(pair_list=i, type_=k)
                    if success:
                        bin_cat_results['analysis_type'] = k
                        results.append(bin_cat_results)

            elif k == 'bin X cont':
                for i in v:
                    success, bin_cont_results = self.bin_x_cont_insights(pair_list=i)
                    if success:
                        bin_cont_results['analysis_type'] = k
                        results.append(bin_cont_results)
                        # bin_var, cont_var = i
                        # bin_unique_values = list(set(self.df[bin_var].values))

                        # # Filter out nans
                        # tmpdf = self.df[self.df[bin_var].notnull() & (self.df[cont_var].notnull())]
                        # _, p2 = stats.ttest_ind(tmpdf[cont_var], tmpdf[bin_var])
                        # if self.only_significant:
                        #     if p2 <= self.siglvl:
                        #         ins = f"{bin_unique_values[0]} and {bin_unique_values[1]} "\
                        #               f"{self.S.plural_noun(self.granularity)} differ in {cont_var}. P val of {p2:.2f}"
                        #         # TODO: {bin_unique_values[0]} are X% lower/higer; {bin_unique_values[0]} average is X times/% higher/lower than {bin_unique_values[1]}
                        #         results.append({
                        #             'date': self.run_date, 'dataset': self.dataset, 'insight_text': ins, 'p_val': p2,
                        #             'magnitude': np.nan, 'col_1': bin_var, 'col_2': cont_var, 'analysis_type': k
                        #         })
                        # else:
                        #     # want to see sig and non sig analysis
                        #     if p2 <= self.siglvl:
                        #         ins = f"{self.S.plural_noun(self.granularity.title())} are different in {cont_var} between"\
                        #               f" {bin_var} groups. P val of {p2:.2f}"
                        #         results.append({
                        #             'date': self.run_date, 'dataset': self.dataset, 'insight_text': ins, 'p_val': p2,
                        #             'magnitude': np.nan, 'col_1': bin_var, 'col_2': cont_var, 'analysis_type': k
                        #         })
                        #     else:
                        #         ins = f"{self.S.plural_noun(self.granularity.title())} have no significant difference in "\
                        #               f"{cont_var} between {bin_var} groups. P val of {p2:.2f}"
                        #         results.append({
                        #             'date': self.run_date, 'dataset': self.dataset, 'insight_text': ins, 'p_val': p2,
                        #             'magnitude': np.nan, 'col_1': bin_var, 'col_2': cont_var, 'analysis_type': k
                        #         })
            elif k == 'cat X cont':
                for i in v:
                    success, cat_cont_results = self.cat_x_cont_insights(pair_list=i)
                    if success:
                        cat_cont_results['analysis_type'] = k
                        results.append(cat_cont_results)

            elif k == 'cont X cont':
                # print('---- cont X cont ---- ')
                # check correlations

                for i in v:
                    col_1, col_2 = i[0], i[1]
                    coef, pval = stats.pearsonr(self.df[col_1], self.df[col_2])
                    if self.only_significant:
                        if pval <= self.siglvl:
                            if coef >= 0.4:
                                ins = f"Strong positive correlation between {self.granularity.title()}{col_1} and " \
                                      f"{col_2} {coef:.2f}. "
                                results.append({
                                    'date': self.run_date, 'dataset': self.dataset, 'insight_text': ins,
                                    'p_val': round(pval, 4), 'magnitude': np.nan, 'col_1': col_1, 'col_2': col_2,
                                    'analysis_type': k
                                })

                            elif coef < -0.4:
                                ins = f"Strong negative correlation between {self.granularity.title()}{col_1} and " \
                                      f"{col_2} {coef:.2f}. "
                                results.append({
                                    'date': self.run_date, 'dataset': self.dataset, 'insight_text': ins,
                                    'p_val': round(pval, 4), 'magnitude': np.nan, 'col_1': col_1, 'col_2': col_2,
                                    'analysis_type': k
                                })
                            elif -0.2 <= coef <= 0.2:
                                ins = f"Weak correlation between {col_1} and {col_2} {coef:.2f}. "
                                results.append({
                                    'date': self.run_date, 'dataset': self.dataset, 'insight_text': ins,
                                    'p_val': round(pval, 4), 'magnitude': np.nan, 'col_1': col_1, 'col_2': col_2,
                                    'analysis_type': k
                                })
                    else:
                        # want to see sig and non sig analysis
                        if coef >= 0.4:
                            ins = f"{col_1} and {col_2} have strong positive correlation of {coef:.2f}. "
                            results.append({
                                'date': self.run_date, 'dataset': self.dataset, 'insight_text': ins,
                                'p_val': round(pval, 4), 'magnitude': np.nan, 'col_1': col_1, 'col_2': col_2,
                                'analysis_type': k
                            })
                        elif coef < -0.4:
                            ins = f"{col_1} and {col_2} have strong negative correlation of {coef:.2f}. "
                            results.append({
                                'date': self.run_date, 'dataset': self.dataset, 'insight_text': ins,
                                'p_val': round(pval, 4), 'magnitude': np.nan, 'col_1': col_1, 'col_2': col_2,
                                'analysis_type': k
                            })
                        else:
                            ins = f"{col_1} and {col_2} little to no correlation of {coef:.2f}. "
                            results.append({
                                'date': self.run_date, 'dataset': self.dataset, 'insight_text': ins,
                                'p_val': round(pval, 4), 'magnitude': np.nan, 'col_1': col_1, 'col_2': col_2,
                                'analysis_type': k
                            })

        results_df = pd.DataFrame(results)
        return results_df

    def main(self):

        # Step 1: run the awesome pandas profiling
        pobject = pp.ProfileReport(self.df)
        des = pobject.get_description()

        # Step 2: identify analytical types of variables
        analytics_df = des['variables']
        type_dict = self.check_for_categorical(analytics_df)

        # Step three: set them into analytical buckets
        analytics_dict = self.create_analytical_buckets(type_dict)

        # Step four: run the analytics!
        self.auto_analysis(d_=analytics_dict)
        return analytics_dict, analytics_df


if __name__ == '__main__':
    ai = AutoInsightsLong()
    d = ai.main()
    print(d)
