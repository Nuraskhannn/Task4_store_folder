import os
import re
import glob
import json
import pandas as pd
import yaml
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

if not os.path.exists(DATA_DIR):
    DATA_DIR = BASE_DIR

NOW_UTC = pd.Timestamp.now(tz='UTC')

def parse_price(val):
    if pd.isna(val):
        return 0.0
    val_str = str(val).strip()
    match = re.search(r'[\d\.]+', val_str)
    if not match:
        return 0.0
    num = float(match.group())
    if '€' in val_str or 'EUR' in val_str.upper():
        return num * 1.2
    return num

def normalize_author_set(author_str):
    if pd.isna(author_str):
        return None
    authors = [a.strip() for a in re.split(r',|&|\band\b', str(author_str)) if a.strip()]
    return ", ".join(sorted(authors))

def robust_parse_timestamps(series):
    raw_str = series.astype(str)
    cleaned = (
        raw_str
        .str.replace(r'A\.M\.', 'AM', regex=True, flags=re.IGNORECASE)
        .str.replace(r'P\.M\.', 'PM', regex=True, flags=re.IGNORECASE)
        .str.replace(r'[;,]', ' ', regex=True)
        .str.strip()
    )
    parsed = pd.Series(index=series.index, dtype='datetime64[ns, UTC]')
    dot_mask = cleaned.str.contains(r'\d{1,2}\.\d{1,2}\.\d{2,4}', regex=True, na=False)
    if dot_mask.any():
        parsed[dot_mask] = pd.to_datetime(
            cleaned[dot_mask], format='mixed', dayfirst=True, errors='coerce', utc=True
        )
    if (~dot_mask).any():
        parsed[~dot_mask] = pd.to_datetime(
            cleaned[~dot_mask], format='mixed', dayfirst=False, errors='coerce', utc=True
        )
    return parsed

store_paths = [p for p in sorted(glob.glob(os.path.join(DATA_DIR, "STORE*"))) if os.path.isdir(p)]

audit_summary = []
all_results = {}

for store_path in store_paths:
    store_name = os.path.basename(store_path)
    
    users = pd.read_csv(os.path.join(store_path, "users.csv")).rename(columns={'id': 'user_id'})
    orders = pd.read_parquet(os.path.join(store_path, "orders.parquet"))

    with open(os.path.join(store_path, "books.yaml"), 'r', encoding='utf-8') as f:
        books_data = yaml.safe_load(f)
    books = pd.DataFrame([{str(k).lstrip(':'): v for k, v in item.items()} for item in books_data]).rename(columns={'id': 'book_id'})

    orders['unit_price_usd'] = orders['unit_price'].apply(parse_price)
    orders['paid_price'] = (orders['quantity'] * orders['unit_price_usd']).round(2)
    
    total_orders = len(orders)
    orders['parsed_ts'] = robust_parse_timestamps(orders['timestamp'])
    
    valid_mask = orders['parsed_ts'].notna() & (orders['parsed_ts'] <= NOW_UTC)
    cnt_future = (orders['parsed_ts'] > NOW_UTC).sum()
    cnt_nat = orders['parsed_ts'].isna().sum()
    cnt_valid = valid_mask.sum()
    
    audit_summary.append({
        'store': store_name,
        'total': total_orders,
        'valid': cnt_valid,
        'future_filtered': cnt_future,
        'nat_unparsed': cnt_nat
    })

    df = orders[valid_mask].merge(users, on='user_id', how='left').merge(books, on='book_id', how='left')

    parent = {uid: uid for uid in users['user_id']}
    def find(i):
        if parent[i] == i:
            return i
        parent[i] = find(parent[i])
        return parent[i]

    def union(i, j):
        root_i = find(i)
        root_j = find(j)
        if root_i != root_j:
            parent[root_i] = root_j

    users_clean = users.fillna('')
    user_records = users_clean.to_dict('records')
    
    buckets = defaultdict(list)
    for idx, u in enumerate(user_records):
        for field in ['name', 'phone', 'email']:
            val = str(u[field]).strip()
            if val:
                buckets[(field, val)].append(idx)

    candidate_pairs = set()
    for idx_list in buckets.values():
        if len(idx_list) > 1:
            for i in range(len(idx_list)):
                for j in range(i + 1, len(idx_list)):
                    candidate_pairs.add((idx_list[i], idx_list[j]))

    for i, j in candidate_pairs:
        u1, u2 = user_records[i], user_records[j]
        diffs = 0
        for field in ['name', 'address', 'phone', 'email']:
            if str(u1[field]) != str(u2[field]):
                diffs += 1
                if diffs > 1:
                    break
        if diffs == 1:
            union(u1['user_id'], u2['user_id'])

    user_to_canonical = {uid: find(uid) for uid in users['user_id']}
    df['canonical_user_id'] = df['user_id'].map(user_to_canonical)
    unique_users_count = len(set(user_to_canonical.values()))

    df['canonical_author_set'] = df['author'].apply(normalize_author_set)
    unique_author_sets_count = df['canonical_author_set'].dropna().nunique()

    popular_author = df.groupby('canonical_author_set')['quantity'].sum().idxmax()

    user_spending = df.groupby('canonical_user_id')['paid_price'].sum()
    best_canonical_id = user_spending.idxmax()
    best_buyer_aliases = sorted([int(uid) for uid, c_id in user_to_canonical.items() if c_id == best_canonical_id])

    df['date'] = df['parsed_ts'].dt.strftime('%Y-%m-%d')
    top5_days = df.groupby('date')['paid_price'].sum().nlargest(5).reset_index()

    daily_rev = df.groupby('date')['paid_price'].sum().reset_index()
    daily_rev['date'] = pd.to_datetime(daily_rev['date'])
    
    min_date = daily_rev['date'].min()
    max_date = daily_rev['date'].max()
    all_dates = pd.date_range(start=min_date, end=max_date, freq='D')
    daily_rev = daily_rev.set_index('date').reindex(all_dates, fill_value=0.0).reset_index()
    daily_rev.columns = ['date', 'paid_price']

    plt.figure(figsize=(10, 4))
    plt.plot(daily_rev['date'], daily_rev['paid_price'], color='tab:blue', linewidth=1.2)
    plt.title(f"Daily Revenue — {store_name}")
    plt.xlabel("Date (UTC)")
    plt.ylabel("Revenue ($)")
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    chart_path = os.path.join(BASE_DIR, f"{store_name}_revenue.png")
    plt.savefig(chart_path, dpi=150)
    plt.close()

    all_results[store_name] = {
        "unique_users": unique_users_count,
        "unique_author_sets": unique_author_sets_count,
        "popular_author": popular_author,
        "best_buyer_ids": best_buyer_aliases,
        "top_5_days": top5_days.to_dict(orient="records")
    }

    print(f"=== {store_name} RESULTS ===")
    print(f"Parsed rows: {cnt_valid}/{total_orders}. Excluded future dates: {cnt_future}")
    print("\n1. Top 5 days by revenue:\n", top5_days.to_string(index=False))
    print("\n2. Unique real users:", unique_users_count)
    print("3. Unique author sets:", unique_author_sets_count)
    print("4. Most popular author/set:", popular_author)
    print("5. Best buyer (aliases/ids):", best_buyer_aliases)
    print(f"6. Chart generated: {store_name}_revenue.png")
    print("-" * 50)

json_out_path = os.path.join(BASE_DIR, "results.json")
with open(json_out_path, "w", encoding="utf-8") as f:
    json.dump(all_results, f, indent=4, ensure_ascii=False)

print("\n=== FINAL AUDIT SUMMARY ===")
audit_df = pd.DataFrame(audit_summary)
print(audit_df.to_string(index=False))
print(f"\nSaved calculation results to: {json_out_path}")