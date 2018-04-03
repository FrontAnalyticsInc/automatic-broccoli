#!/usr/bin/env python
from scipy import stats
import numpy as np
import pandas as pd


def binary_checker(column, unique_values):
    """Hackish way of negating the column name. For example, if the column were "active" and the values were False, True
    then we change the crosstab labels from False, True to "non-active" "active".

    Args:
        column: str, the name of the column that has a binary/boolean characteristic
        unique_values: list, the unique values in said column

    Returns:
        bool, str, str
    """
    check1 = sum([isinstance(i, (bool, np.bool_)) for i in unique_values]) == 2
    check2 = all([isinstance(i, (int, np.uint8)) for i in unique_values]) and sum(unique_values) == 1
    if check1 or check2:
        return True, 'non-'+str(column), str(column)  # Hack negation of the column name
    else:
        print('not a binary value?')
        return False, "", ""


def label_stuff(x):
    # TODO: can I make this dynamic?
    if 0 < x <= 0.25:
        return "low"
    elif 0.25 < x <= 0.75:
        return "medium"
    else:
        return "high"


def cool_crosstabs(xtab, cat_column_name) -> str:
    """Runs a series of checks on the cross tab to look for insights!

    Args:
        xtab: pandas DataFrame, the crosstab with the categorical options on the index and the binary on the columns
        cat_column_name: str, the categorical column name, used for saying what's going on

    Returns:
        str, an insights string
    """
    # - findings
    bin1 = xtab.columns[0]
    bin2 = xtab.columns[1]
    # max/min categories
    bin1_max_cat = xtab[bin1].idxmax()
    bin2_max_cat = xtab[bin2].idxmax()
    bin1_min_cat = xtab[bin1].idxmin()
    bin2_min_cat = xtab[bin2].idxmin()
    # max/min values
    bin1_max_val = xtab.loc[bin1_max_cat, bin1]
    bin2_max_val = xtab.loc[bin2_max_cat, bin2]
    bin1_min_val = xtab.loc[bin1_min_cat, bin1]
    bin2_min_val = xtab.loc[bin2_min_cat, bin2]
    # values for each binary category
    v1 = xtab[xtab.columns[0]].values
    v2 = xtab[xtab.columns[1]].values

    insights = ""

    # The same value for a given index
    same_val_for_cat = xtab.index[xtab[bin1] == xtab[bin2]]  # [0]
    if same_val_for_cat.shape[0] > 0:
        val_same = xtab.loc[same_val_for_cat[0], bin1]
        insights += f'Both {bin1} and {bin2} have a value of {val_same} for {same_val_for_cat[0]}. '

    # average diff
    # xtab['perc_diff'] = (xtab[bin1] - xtab[bin2]) / (xtab[bin1] + xtab[bin2])
    # avg_delta = xtab['perc_diff'].mean()

    # insights checker
    if bin1_max_cat == bin2_max_cat:
        insights += f'{bin1_max_cat} is the top category for both {bin1} at {bin1_max_val} and {bin2} at ' \
                    f'{bin2_max_val} for {cat_column_name}. '

    if bin1_max_cat == bin2_min_cat:
        insights += f'{bin1.title()} and {bin2.title()} are the farthest apart on {bin1_max_cat} in ' \
                    f'{cat_column_name}. {bin1.title()} maximum on {bin1_max_cat} is {bin1_max_val} and ' \
                    f'{bin2} minimum is on {bin1_max_cat} at {bin2_min_val}. '

    if bin2_max_cat == bin1_min_cat:
        insights += f'{bin2.title()} and {bin1.title()} are the farthest apart on {bin2_max_cat} in ' \
                    f'{cat_column_name}. {bin2.title()} maximum on {bin2_max_cat} is {bin2_max_val} and ' \
                    f'{bin1} minimum is on {bin2_max_cat} at {bin1_min_val}. '

    # slope checker
    slope, intercept, r_value, p_value, std_err = stats.linregress(v1, v2)
    if slope <= -1.5:
        insights += f'{bin2.title()} and {bin1.title()} seem to have diverging frequencies. '

    elif slope >= 1.5:
        insights += f'{bin2.title()} and {bin1.title()} seem to have similar frequencies. '

    return insights


def tight_t_test(bin_var, cont_var, bin_unique_values, pos_desc, neg_desc, cv_tol=0.15):
    """
        Runs a series of checks for a group of binary variables testing on a continuous variable to look for insights!
        Calculates the Coeficient of Variation: https://en.wikipedia.org/wiki/Coefficient_of_variation
        Args:
            bin_var: str, the column name of the binary variable
            cont_var: str, the column name of the continuous variable
            bin_unique_values: list, the unique values of the binary variable. Should be 0,1 or True, False
            pos_desc: pandas.core.series.Series, the descriptive statistics for the positive class
            neg_desc: pandas.core.series.Series, the descriptive statistics for the negative class
            cv_tol: float, if values are less than this, we consider them the same

        Returns:
            str, an insights string
        """
    success, bin_label_0, bin_label_1 = binary_checker(bin_var, bin_unique_values)
    if success:
        insight = ""
        if pos_desc['min'] > 0 and neg_desc['min'] > 0:
            cv_neg = neg_desc['std'] / neg_desc['mean']
            cv_pos = pos_desc['std'] / pos_desc['mean']

            # magnitude of variability
            neg_variability = label_stuff(cv_neg)
            pos_variability = label_stuff(cv_pos)

            if np.isclose(cv_neg, cv_pos, rtol=cv_tol):
                insight += f"Both {bin_label_1.title()} and {bin_label_0.title()} have a {pos_variability} " \
                           f"level of variability on {cont_var}. {bin_label_1.title()} average is " \
                           f"{pos_desc['mean']:.1f} and {bin_label_0.title()} average is {neg_desc['mean']:.1f}. "
            elif cv_pos > cv_neg:
                insight += f"{bin_label_1.title()} has a higher variability in {cont_var} of {cv_pos:.2f} " \
                           f"whereas {bin_label_0} is more stable at {cv_neg:.2f}. "
            elif cv_pos < cv_neg:
                insight += f"{bin_label_0.title()} has a higher variability in {cont_var} of {cv_neg:.2f} " \
                           f"whereas {bin_label_1.title()} is more stable at {cv_pos:.2f}. "
        elif np.isclose(pos_desc['std'], neg_desc['std'], rtol=cv_tol):
            insight += f"{bin_label_0.title()} and {bin_label_1.title()} have basically the same spread around " \
                       f"their means of {pos_desc['std']:.2f} and {neg_desc['std']:.2f}. "

        else:
            if pos_desc['std'] > neg_desc['std']:
                insight += f"{bin_label_1.title()} has a higher spread (std) in {cont_var} of {pos_desc['std']:.2f} " \
                           f"whereas {bin_label_0.title()} is more stable at {neg_desc['std']:.2f}. "
            else:
                insight += f"{bin_label_0.title()} has a higher spread (std) in {cont_var} of {neg_desc['std']:.2f} " \
                           f"whereas {bin_label_1.title()} is more stable at {pos_desc['std']:.2f}. "

        return insight


def cool_categories():
    return "THERE WILL BE SOMETHING HERE SOON"
