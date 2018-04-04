#!/usr/bin/env python
from scipy import stats
import numpy as np
import re

"""Helper funcs for auto broccoli"""


def label_stuff(x):
    # TODO:  make this dynamic?
    if 0 < x <= 0.25:
        return "low"
    elif 0.25 < x <= 0.75:
        return "medium"
    else:
        return "high"


def id_column_check(string):
    """Takes in a column and returns a check to see if it thinks it's an identifier column"""
    success = re.match(r'\w*ID|\w*Id|\w*_ID|\w*_Id|\w*_id|account', string, re.IGNORECASE)
    if success:
        return True
    else:
        return False


def check_list_is_contiguous(list_of_ints) -> bool:
    """Checks that a list of ints is contiguous
    https://stackoverflow.com/questions/28885455/python-check-whether-list-is-sequential-or-not
    """
    sorted_list = sorted(list_of_ints)
    it = (x for x in sorted_list)
    first = next(it)
    return all(a == b for a, b in enumerate(it, first + 1))


def crosstabs_on_binary_v_categorical(xtab, cat_column_name) -> str:
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
                    f'{bin2_max_val} for "{cat_column_name}". '

    if bin1_max_cat == bin2_min_cat:
        insights += f'{bin1.title()} and {bin2.title()} are the farthest apart on "{bin1_max_cat}" in ' \
                    f'"{cat_column_name}". {bin1.title()} maximum on {bin1_max_cat} is {bin1_max_val} and ' \
                    f'{bin2} minimum is on {bin1_max_cat} at {bin2_min_val}. '

    if bin2_max_cat == bin1_min_cat:
        insights += f'{bin2.title()} and {bin1.title()} are the farthest apart on "{bin2_max_cat}" in ' \
                    f'"{cat_column_name}". {bin2.title()} maximum on {bin2_max_cat} is {bin2_max_val} and ' \
                    f'{bin1} minimum is on {bin2_max_cat} at {bin1_min_val}. '

    # slope checker
    slope, intercept, r_value, p_value, std_err = stats.linregress(v1, v2)
    if slope <= -1.5:
        insights += f'{bin2.title()} and {bin1.title()} seem to have diverging frequencies. '

    elif slope >= 1.5:
        insights += f'{bin2.title()} and {bin1.title()} seem to have similar frequencies. '

    return insights


def independent_t_test(bin_label_0, bin_label_1, cont_var, pos_desc, neg_desc, cv_tol=0.15):
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
    insight = ""
    if pos_desc['min'] > 0 and neg_desc['min'] > 0:
        cv_neg = neg_desc['std'] / neg_desc['mean']
        cv_pos = pos_desc['std'] / pos_desc['mean']

        # magnitude of variability
        neg_variability = label_stuff(cv_neg)
        pos_variability = label_stuff(cv_pos)

        if np.isclose(cv_neg, cv_pos, rtol=cv_tol):
            insight += f'Both {bin_label_1.title()} and {bin_label_0.title()} have a {pos_variability} ' \
                       f'level of variability on "{cont_var}". {bin_label_1.title()} average is ' \
                       f"{pos_desc['mean']:.1f} and {bin_label_0.title()} average is {neg_desc['mean']:.1f}. "
        elif cv_pos > cv_neg:
            insight += f'{bin_label_1.title()} has a higher variability in "{cont_var}" of {cv_pos:.2f} ' \
                       f'whereas {bin_label_0} is more stable at {cv_neg:.2f}. '
        elif cv_pos < cv_neg:
            insight += f"{bin_label_0.title()} has a higher variability in {cont_var} of {cv_neg:.2f} " \
                       f"whereas {bin_label_1.title()} is more stable at {cv_pos:.2f}. "
    elif np.isclose(pos_desc['std'], neg_desc['std'], rtol=cv_tol):
        insight += f'{bin_label_0.title()} and {bin_label_1.title()} have basically the same spread around ' \
                   f'their means of {pos_desc["std"]:.2f} and {neg_desc["std"]:.2f} on "{cont_var}". '

    else:
        if pos_desc['std'] > neg_desc['std']:
            insight += f'{bin_label_1.title()} has a higher spread (std) in "{cont_var}" of {pos_desc["std"]:.2f} '\
                       f'whereas {bin_label_0.title()} is more stable at {neg_desc["std"]:.2f}. '
        else:
            insight += f'{bin_label_0.title()} has a higher spread (std) in "{cont_var}" of {neg_desc["std"]:.2f} '\
                       f'whereas {bin_label_1.title()} is more stable at {pos_desc["std"]:.2f}. '

    return insight


def correlations(insights, coef, pval, pval_threshold, col_1, col_2):
    """"""
    if pval <= pval_threshold:
        if coef <= -0.35:
            insights += f"As {col_1} increases {col_2} decreases with coef of {coef:.2f}. "
        elif -0.35 < coef <= 0.35:
            insights += f" with coef of {coef:.2f}."
        elif 0.35 < coef <= 0.75:
            insights += f"As {col_1} increases {col_2} increases with coef of {coef:.2f}. "
        elif coef > 0.75:
            insights += f"{col_1} increases nearly linearly with respect to {col_2}. "
    else:
        insights += f"Not likely a linear relationship in {col_1} in {col_2} with with coef of {coef:.2f}"
    return insights


def analyze_xtab_column_frequency(xtab, b_dict, label, threshold=0.2):
    """"""
    columns = b_dict.get(label)
    if columns is not None and isinstance(columns, list):
        insights = ""
    else:
        raise KeyError(f"{label} not found in b_dict")
    for i, column in enumerate(columns):
        top_row_val    = xtab[columns[i]].values[0]
        bottom_row_val = xtab[columns[i]].values[1]
        diff = np.abs(top_row_val - bottom_row_val)
        if diff >= threshold:
            max_class = xtab[columns[i]].idxmax()  # which index class has the majority?
            insights += f"'{max_class.title()}' rows have {diff*100:.1f}% of '{columns[i]}'. "
    return insights

def cool_categories():
    return "Coming soon"