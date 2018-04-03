# automatic-broccoli :crystal_ball:

> "You need to write SQL to analyze a database"  
 Automatic Broccoli is there for when you don't know what to look for yet; for when you don't know what exists so you can't write the SQL. 

## Why?
We wanted to create a data product to support hard-coded dashboard logic by running tests on things we didn't hard code in the background. To run asyncronously to other jobs / queries while using clever caching for speed and retrieval to ask questions and find connections and useful insights.

## Prior Art
[Pandas Profiling](https://github.com/pandas-profiling/pandas-profiling) has done a lot of the heavy lifting for doing inital dataset exploratory data analysis (EDA). It does a great job of generating profile reports in HTML format for a dataset, saving an analyst a lot of time going through that process on their own. This project builds on top of the shoulders of Pandas Profiling by going a few steps further.

## How is Automatic Broccoli different?
Current tools do a great job of identifying the datatype of a column, like a numeric, date, string, etc. Using that knowledge descriptive stats can be produced...and that's about where it stops.

Automatic Broccoli goes further in attempting to identify not only the type of column, but its analytical possibilities, especially in relation to the other columns present. Currently, it can detect if a column is a binary, categorical, or continuous and then prepares a dictionary of possible unique combinations of analyses that can be tested. 

## Example

```python
>>> from auto_insights import AutoInsightsLong
>>> import pandas_profiling as pp

>>> ai = AutoInsightsLong(df=None)  # if df=None, it autogenerates it's own data

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

analysis_type  |  col_1             |  col_2             |  date              |  insight_text                                                                                                                                                                                                                                                                                                                                      |  p_val
---------------|--------------------|--------------------|--------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------
bin X cat      |  active            |  buyer_type        |  2018-04-03 11:29  |  Other is the top category for both non-active at 129 and active at 153 for buyer_type. Active and Non-Active seem to have similar frequencies.                                                                                                                                                                                                    |  0.6521
bin X cat      |  active            |  content_type      |  2018-04-03 11:29  |  Both non-active and active have a value of 105 for Social Media. Active and Non-Active are the farthest apart on Newspaper in content_type. Active maximum on Newspaper is 109 and non-active minimum is on Newspaper at 85.                                                                                                                      |  0.691
bin X cat      |  nice_person       |  buyer_type        |  2018-04-03 11:29  |  Other is the top category for both non-nice_person at 134 and nice_person at 148 for buyer_type. Nice_Person and Non-Nice_Person seem to have similar frequencies.                                                                                                                                                                                |  0.8197
bin X cat      |  nice_person       |  content_type      |  2018-04-03 11:29  |  Both non-nice_person and nice_person have a value of 99 for Doubleclick.                                                                                                                                                                                                                                                                          |  0.3458
bin X cont     |  active            |  duration_percent  |  2018-04-03 11:29  |  Both Active and Non-Active have a medium level of variability on duration_percent. Active average is 53.2 and Non-Active average is 51.9.                                                                                                                                                                                                         |  0.4971
bin X cont     |  active            |  impressions       |  2018-04-03 11:29  |  Both Active and Non-Active have a medium level of variability on impressions. Active average is 3.0 and Non-Active average is 2.9.                                                                                                                                                                                                                |  0.0959
bin X cont     |  active            |  visits            |  2018-04-03 11:29  |  Non-Active and Active have basically the same spread around their means of 291.28 and 283.72.                                                                                                                                                                                                                                                     |  0.8563
bin X cont     |  nice_person       |  duration_percent  |  2018-04-03 11:29  |  Both Nice_Person and Non-Nice_Person have a medium level of variability on duration_percent. Nice_Person average is 52.7 and Non-Nice_Person average is 52.4.                                                                                                                                                                                     |  0.8635
bin X cont     |  nice_person       |  impressions       |  2018-04-03 11:29  |  Both Nice_Person and Non-Nice_Person have a medium level of variability on impressions. Nice_Person average is 3.0 and Non-Nice_Person average is 2.9.                                                                                                                                                                                            |  0.5986
bin X cont     |  nice_person       |  visits            |  2018-04-03 11:29  |  Non-Nice_Person and Nice_Person have basically the same spread around their means of 283.93 and 290.90.                                                                                                                                                                                                                                           |  0.1642
cat X cont     |  buyer_type        |  duration_percent  |  2018-04-03 11:29  |  Coming soon                                                                                                                                                                                                                                                                                                                                       |  0.0502
cat X cont     |  buyer_type        |  impressions       |  2018-04-03 11:29  |  Coming soon                                                                                                                                                                                                                                                                                                                                       |  0.7561
cat X cont     |  buyer_type        |  visits            |  2018-04-03 11:29  |  Coming soon                                                                                                                                                                                                                                                                                                                                       |  0.4173
cat X cont     |  content_type      |  duration_percent  |  2018-04-03 11:29  |  Coming soon                                                                                                                                                                                                                                                                                                                                       |  0.7452
cat X cont     |  content_type      |  impressions       |  2018-04-03 11:29  |  Coming soon                                                                                                                                                                                                                                                                                                                                       |  0.3218
cat X cont     |  content_type      |  visits            |  2018-04-03 11:29  |  Coming soon                                                                                                                                                                                                                                                                                                                                       |  0.6531
cont X cont    |  duration_percent  |  impressions       |  2018-04-03 11:29  |  duration_percent and impressions little to no correlation of -0.02.                                                                                                                                                                                                                                                                               |  0.4921
cont X cont    |  duration_percent  |  visits            |  2018-04-03 11:29  |  duration_percent and visits little to no correlation of 0.02.                                                                                                                                                                                                                                                                                     |  0.4418
cont X cont    |  impressions       |  visits            |  2018-04-03 11:29  |  impressions and visits little to no correlation of 0.01.                                                                                                                                                                                                                                                                                          |  0.8076
bin X bin      |  active            |  nice_person       |  2018-04-03 11:29  |  Non-Active and Active are the farthest apart on nice_person in nice_person. Non-Active maximum on nice_person is 260 and active minimum is on nice_person at 247. Active and Non-Active are the farthest apart on non-nice_person in nice_person. Active maximum on non-nice_person is 271 and non-active minimum is on non-nice_person at 222.   |  0.0555
 
## TODO:
 - Testing!
 - Better date handling
 - Add connections across tables (2+) tables instead of just one table
 - Setup meta database of 
 - Setup input tags for dataset types such as "marketing", "social media" etc.
 
# License
Copyright (c) 2017 Front Analytics Inc. Licensed under [the MIT License](http://opensource.org/licenses/MIT).
