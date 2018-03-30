#!/usr/bin/env python
# -*- encoding: utf-8 -*-

"""http://faker.readthedocs.io/en/master/providers/faker.providers.address.html?highlight=random"""

import pandas_profiling as pp
import pandas as pd
from faker import Factory
from datetime import datetime
import random
from scipy import stats
import re
import sys
from collections import defaultdict
import itertools
from src.inflect import inflect


class AutoInsightsLong(object):
    """Designed for long data"""
    def __init__(self, df=None, categorical_as_ints=False, only_significant=False, sig_level=0.05, min_samples=30):
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
        self.content_piece = 'video,article,social_media'.split(',')
        self.cat_ordinal = [1, 2, 3, 4, 5]
        if df is not None:
            self.df = df
        else:
            self.df = pd.DataFrame([self.example_record() for _ in range(1000)])
        self.granularity = self.intro()

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
        return {'user_id': self.faker.ascii_email(),  # random user email
                'active': self.faker.boolean(),  # random status
                'buyer_type': random.choice(['me', 'spouse', 'friend', 'other']),
                'some_category': random.choice(self.cat_ordinal),
                'content_type': random.choice(self.content_piece),  # video,article,social_media
                'visits': self.faker.random_number(3),  # id's eg:1,20,28,27
                'date': self.date_between('mar01-2018', 'mar30-2018'),  # datetime between mar01-2015 to mar15-2015
                'duration_percent': round(random.uniform(1, 100), 3)  # watch duration perc
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

    def auto_analysis(self, d_):
        """"""
        # TODO: write out the results to a pandas dataframe instead of printing
        for k, v in d_.items():
            if k == 'bin X cat' or k == 'bin X bin':
                print('---- Running bin X cat ---- ')
                # run chi-square test
                for i in v:
                    bin_var, cat_var = i
                    cat_unique_values = list(set(self.df[cat_var].values))
                    xtab_clean = pd.crosstab(self.df[cat_var], self.df[bin_var])
                    xtab_read = pd.crosstab(self.df[cat_var], self.df[bin_var], normalize='index')
                    chi2, p, dof, expected = stats.chi2_contingency(xtab_clean)
                    if self.only_significant:
                        if p <= self.siglvl:
                            print(f"significant difference in {cat_var} between {self.S.join(cat_unique_values)} groups. P val of {p:.2f}")
                    else:
                        # want to see sig and non sig analysis
                        if p <= self.siglvl:
                            print(f"{self.granularity.title()} are different in {cat_var} between {bin_var} groups. P val of {p:.2f}")
                            # TODO: bin group 1 is X% higher in cat group Z
                        else:
                            print(f"{self.granularity.title()} have no significant difference in {self.S.join(cat_unique_values)} between {bin_var} groups. P val of {p:.2f}")

            elif k == 'bin X cont':
                print('---- Running bin X cont ---- ')
                for i in v:
                    bin_var, cont_var = i
                    bin_unique_values = list(set(self.df[bin_var].values))
                    # Filter out nans
                    tmpdf = self.df[self.df[bin_var].notnull() & (self.df[cont_var].notnull())]
                    _, p2 = stats.ttest_ind(tmpdf[cont_var], tmpdf[bin_var])
                    if self.only_significant:
                        if p2 <= self.siglvl:
                            print(f"{bin_unique_values[0]} and {bin_unique_values[1]} {self.S.plural_noun(self.granularity)} differ in {cont_var}. P val of {p2:.2f}")
                            # TODO: {bin_unique_values[0]} are X% lower/higer; {bin_unique_values[0]} average is X times/% higher/lower than {bin_unique_values[1]}
                    else:
                        # want to see sig and non sig analysis
                        if p2 <= self.siglvl:
                            print(f"{self.S.plural_noun(self.granularity.title())} are different in {cont_var} between {bin_var} groups. P val of {p2:.2f}")
                        else:
                            print(f"{self.S.plural_noun(self.granularity.title())} have no significant difference in {cont_var} between {bin_var} groups. P val of {p2:.2f}")

            elif k == 'cat X cont':
                print('---- Running cat X cont ---- ')
                for i in v:
                    cat_var, cont_var = i
                    tmpdf = self.df[self.df[cat_var].notnull() & (self.df[cont_var].notnull())]  # Filter out nans
                    try:
                        # Anova
                        grps = pd.unique(tmpdf[cat_var].values)
                        d_data = {grp: tmpdf[cont_var][tmpdf[cat_var] == grp] for grp in grps}
                        f, p = stats.f_oneway(*d_data.values())
                    except Exception as e:
                        print('*** ', e.args, f'{cont_var} and {cat_var}')
                        print()
                    else:
                        if self.only_significant:
                            if p <= self.siglvl:
                                print(f"{self.granularity.title()} are different in {cont_var} between {cat_var} groups. P val of {p:.3f}")
                        else:
                            # want to see sig and non sig analysis
                            if p <= self.siglvl:
                                print(f"{self.granularity.title()} are different in {cont_var} between {cat_var} groups. P val of {p:.3f}")
                            else:
                                print(f"{self.granularity.title()} have no significant difference in {cont_var} between {cat_var} groups. P val of {p:.3f}")

            elif k == 'cont X cont':
                print('---- cont X cont ---- ')
                # check correlations

                for i in v:
                    col_1, col_2 = i[0], i[1]
                    coef, pval = stats.pearsonr(self.df[col_1], self.df[col_2])
                    if self.only_significant:
                        if pval <= self.siglvl:
                            if coef >= 0.4:
                                print(f"Strong positive correlation between {self.granularity.title()}{col_1} and {col_2} {coef:.2f}. P val of {pval:.2f}")
                            elif coef < -0.4:
                                print(f"Strong negative correlation between {col_1} and {col_2} {coef:.2f}. P val of {pval:.2f}")
                            elif -0.2 <= coef <= 0.2:
                                print(f"Weak correlation between {col_1} and {col_2} {coef:.2f}. P val of {pval:.2f}")
                    else:
                        # want to see sig and non sig analysis
                        if coef >= 0.4:
                            print(f"{col_1} and {col_2} have strong positive correlation of {coef:.2f}. P val of {pval:.2f}")
                        elif coef < -0.4:
                            print(f"{col_1} and {col_2} have strong negative correlation of {coef:.2f}. P val of {pval}")
                        else:
                            print(f"{col_1} and {col_2} little to no correlation of {coef:.2f}. P val of {pval:.2f}")

            print()
        return None

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
