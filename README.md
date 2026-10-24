# Multi-Store Analytics Pipeline and Dashboard

This project processes and cleans the data of five online stores (STORE1 - STORE5), calculates some business metrics for each of them and shows the results in a Streamlit dashboard with a simple text chat.

## What was done

The project has two parts.

### Part 1: data processing (merge.py)

- Prices and currencies. Prices come in different formats (with the symbols € and EUR), so the script parses them and converts everything to dollars with the rate 1 EUR = 1.2 USD.
- Merging duplicate users. Some users appear several times with a changed address, phone, email or alias instead of a real name. I used the union-find algorithm (disjoint set union) to join users who have the same name, phone or email and differ in at most one field. This gives the number of real unique users and helps to find the best buyer (top customer by total money spent) with all of his ids.
- Authors. Author names are cleaned and sorted, so the order of names does not matter. This is used to count unique sets of authors and to find the most popular author or set of authors.
- Time series and charts. The script calculates daily revenue, fills the days without sales with zeros and saves a chart for each store (STOREx_revenue.png).
- Export. All results are saved to one file, results.json, and the dashboard loads them from there.

### Part 2: dashboard (app.py)

- One tab for each store, STORE1 - STORE5.
- Each tab shows the number of unique users, the number of author sets, the ids of the best buyer, the most popular author, a table with the top 5 days by revenue and the daily revenue chart.
- A chat in the sidebar. It is a simple local parser, not an AI model. It looks for the store name and keywords in the question (buyer, author, users, revenue) and answers with data from results.json. It does not use any external API. Questions about other topics are not supported, and the AI control of the dashboard (part 3 of the task) is not done.

## The date problem

When I made the first charts, there was a huge spike of revenue in the last days. After checking the timestamps in orders.parquet I found that the data has two different date formats:

1. DD.MM.YYYY with dots, for example 11.04.2026 is 11 April.
2. MM/DD/YYYY with slashes, for example 01/31/25 is 31 January.

Also, some rows have the time before the date and write A.M. / P.M. with extra dots.

At first all the dates were parsed in the same way, so the dotted dates were read as month/day. Because of this some orders landed in the future and others ended up on the wrong days.

How it was fixed. The function parse_timestamps in merge.py now does this:

- changes A.M. / P.M. to AM / PM and cleans extra separators before parsing;
- parses dates with dots with dayfirst=True;
- parses dates with slashes with dayfirst=False;
- removes orders with a date later than the moment when the script is run.

I checked the formats on the real data: in dotted dates the second number is never bigger than 12, and in slashed dates the first number is never bigger than 12. After the fix all the rows in all 5 stores were parsed (no unparsed dates and no dates from the future).

## Libraries

- pandas - loading, cleaning and aggregating the data
- pyarrow - reading the parquet file (orders.parquet)
- pyyaml - reading the yaml file (books.yaml)
- matplotlib - drawing the revenue charts and saving them as png
- streamlit - the web dashboard

All of them are listed in requirements.txt.

## How to run

1. Install the libraries. Open a terminal in the project folder and run:

```
pip install -r requirements.txt
```

2. Run the processing script (it automatically locates the `data/` folder, cleans the dataset, and generates `results.json` along with the PNG charts):
   ```bash
   python merge.py

3. Start the Streamlit dashboard:

```
streamlit run app.py
```

If the system says that the command streamlit is not found (a problem with PATH), run it like this:

```
python -m streamlit run app.py
```

app.py, results.json and the png files must be in the same folder.
