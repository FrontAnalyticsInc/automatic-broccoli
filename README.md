# Automatic Broccoli
Because Broccoli is good for you, and so is this repo! 

## Why?
You need to write SQL to analyze a database. Often times an ad-hoc analysis findings can lead to hard-coded relationships that get put into dashboards excluding relationships that might not have been found or non-existent at the time of the analysis.
We wanted to create a data product to support hard-coded dashboard logic by running tests on things we didn't hard code in the background. To run asyncronously to other jobs / queries to ask questions and find connections and useful insights.

## Prior Art
[Pandas Profiling](https://github.com/pandas-profiling/pandas-profiling) has done a lot of the heavy lifting for doing inital dataset exploratory data analysis (EDA). It does a great job of generating profile reports in HTML format for a dataset, saving an analyst a lot of time going through that process on their own. This project builds on top of the shoulders of Pandas Profiling by going a few steps further.

#### How is Automatic Broccoli different?
Current tools do a great job of identifying the datatype of a column, like a numeric, date, string, etc. Using that knowledge descriptive stats can be produced...and that's about where it stops.

Automatic Broccoli goes further in attempting to identify not only the type of column, but its analytical possibilities, especially in relation to the other columns present. Currently, it can detect if a column is a binary, categorical, or continuous and then prepares a dictionary of possible unique combinations of analyses that can be tested. 

## Example

```python
>>> from auto_broccoli import AutoBroccoli
>>> import pandas_profiling as pp

>>> ai = AutoBroccoli(df=None)  # if df=None, it autogenerates it's own data

>>> # Step 1: run the awesome pandas profiling
>>> pobject = pp.ProfileReport(ai.df)
>>> des = pobject.get_description()

>>> # Step 2: identify analytical types of variables
>>> analytics_df = des['variables']
>>> type_dict = ai.classify_column_types(analytics_df)
>>> type_dict
{'binary': ['active', 'nice_person'],
 'categorical': ['buyer_type', 'content_type'],
 'continuous': ['duration_percent', 'impressions', 'visits'],
 'date': ['date'],
 'high_cardinality': ['user_id']}
```
Notice how it classified the columns for their analytical potential. Then you can create the analytical buckets like this:
```python
>>> # Step three: set them into analytical buckets
>>> analytics_dict = ai.create_analytical_buckets(type_dict)
>>> analytics_dict
{'bin X bin': [('active', 'nice_person')],
 'bin X cat': [['active', 'buyer_type'],
  ['active', 'content_type'],
  ['nice_person', 'buyer_type'],
  ['nice_person', 'content_type']],
 'bin X cont': [['active', 'duration_percent'],
  ['active', 'some_category'],
  ['active', 'visits'],
  ['nice_person', 'duration_percent'],
  ['nice_person', 'some_category'],
  ['nice_person', 'visits']],
 'cat X cont': [['buyer_type', 'duration_percent'],
  ['buyer_type', 'some_category'],
  ['buyer_type', 'visits'],
  ['content_type', 'duration_percent'],
  ['content_type', 'some_category'],
  ['content_type', 'visits']],
 'cont X cont': [('duration_percent', 'some_category'),
  ('duration_percent', 'visits'),
  ('some_category', 'visits')]}
```
An analytics dataframe can then be generated, yielding the columns that were used and the insight(s) found, if any. Other columns exist but weren't included in this example due to space constraints.
```python
>>> # Step four: run the analytics!
>>> resultsdf = ai.auto_analysis(d_=analytics_dict)
resultsdf
```

analysis      |  analysis_type  |  col_1             |  col_2             |  dataset  |  date      |  insight_text                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |  p_val
--------------|-----------------|--------------------|--------------------|-----------|------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------
Chi-square    |  bin X cat      |  active            |  buyer_type        |  random   |  04-04-18  |  Both non-active and active have a value of 127 for Other. Spouse is the top category for both non-active at 130 and active at 137 for "buyer_type". Active and Non-Active seem to have similar frequencies.                                                                                                                                                                                                                                                                     |  0.931
Chi-square    |  bin X cat      |  active            |  content_type      |  random   |  04-04-18  |  Active and Non-Active are the farthest apart on "Doubleclick" in "content_type". Active maximum on Doubleclick is 105 and non-active minimum is on Doubleclick at 90.                                                                                                                                                                                                                                                                                                           |  0.6876
Chi-square    |  bin X cat      |  nice_person       |  buyer_type        |  random   |  04-04-18  |  Non-Nice_Person and Nice_Person are the farthest apart on "Me" in "buyer_type". Non-Nice_Person maximum on Me is 126 and nice_person minimum is on Me at 105.                                                                                                                                                                                                                                                                                                                   |  0.1658
Chi-square    |  bin X cat      |  nice_person       |  content_type      |  random   |  04-04-18  |  Significant difference in 'non-nice_person' and 'nice_person' between 'content_type' groups. Non-Nice_Person and Nice_Person are the farthest apart on "Newspaper" in "content_type". Non-Nice_Person maximum on Newspaper is 111 and nice_person minimum is on Newspaper at 92. Nice_Person and Non-Nice_Person are the farthest apart on "Social Media" in "content_type". Nice_Person maximum on Social Media is 126 and non-nice_person minimum is on Social Media at 88.   |  0.0421
T-test        |  bin X cont     |  active            |  duration_percent  |  random   |  04-04-18  |  Both Active and Non-Active have a medium level of variability on "duration_percent". Active average is 0.3 and Non-Active average is 0.3.                                                                                                                                                                                                                                                                                                                                       |  0.8108
T-test        |  bin X cont     |  active            |  impressions       |  random   |  04-04-18  |  Both Active and Non-Active have a medium level of variability on "impressions". Active average is 3.0 and Non-Active average is 3.0.                                                                                                                                                                                                                                                                                                                                            |  0.9334
T-test        |  bin X cont     |  active            |  visits            |  random   |  04-04-18  |  Non-Active and Active have basically the same spread around their means of 289.37 and 284.37 on "visits".                                                                                                                                                                                                                                                                                                                                                                       |  0.2707
T-test        |  bin X cont     |  nice_person       |  duration_percent  |  random   |  04-04-18  |  Both Nice_Person and Non-Nice_Person have a medium level of variability on "duration_percent". Nice_Person average is 0.3 and Non-Nice_Person average is 0.3.                                                                                                                                                                                                                                                                                                                   |  0.9254
T-test        |  bin X cont     |  nice_person       |  impressions       |  random   |  04-04-18  |  Both Nice_Person and Non-Nice_Person have a medium level of variability on "impressions". Nice_Person average is 3.0 and Non-Nice_Person average is 2.9.                                                                                                                                                                                                                                                                                                                        |  0.3874
T-test        |  bin X cont     |  nice_person       |  visits            |  random   |  04-04-18  |  Non-Nice_Person and Nice_Person have basically the same spread around their means of 283.23 and 290.87 on "visits".                                                                                                                                                                                                                                                                                                                                                             |  0.3585
Anova         |  cat X cont     |  buyer_type        |  duration_percent  |  random   |  04-04-18  |  Coming soon                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |  0.9556
Anova         |  cat X cont     |  buyer_type        |  impressions       |  random   |  04-04-18  |  Coming soon                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |  0.8558
Anova         |  cat X cont     |  buyer_type        |  visits            |  random   |  04-04-18  |  Coming soon                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |  0.144
Anova         |  cat X cont     |  content_type      |  duration_percent  |  random   |  04-04-18  |  Coming soon                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |  0.4053
Anova         |  cat X cont     |  content_type      |  impressions       |  random   |  04-04-18  |  Coming soon                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |  0.4027
Anova         |  cat X cont     |  content_type      |  visits            |  random   |  04-04-18  |  Coming soon                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |  0.9779
Pearson corr  |  cont X cont    |  duration_percent  |  impressions       |  random   |  04-04-18  |  Not likely a linear relationship in duration_percent in impressions with with coef of -0.02                                                                                                                                                                                                                                                                                                                                                                                     |  0.4723
Pearson corr  |  cont X cont    |  duration_percent  |  visits            |  random   |  04-04-18  |  Not likely a linear relationship in duration_percent in visits with with coef of -0.01                                                                                                                                                                                                                                                                                                                                                                                          |  0.8102
Pearson corr  |  cont X cont    |  impressions       |  visits            |  random   |  04-04-18  |  Not likely a linear relationship in impressions in visits with with coef of 0.05                                                                                                                                                                                                                                                                                                                                                                                                |  0.0853
 
## TODO:
 - Testing!
 - Better date handling
 - Add connections across tables (2+) tables instead of just one table
 - Setup meta database of 
 - Setup input tags for dataset types such as "marketing", "social media" etc.
 
# License
Copyright (c) 2017 Front Analytics Inc. Licensed under [the MIT License](http://opensource.org/licenses/MIT).
