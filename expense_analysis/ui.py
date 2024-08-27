import streamlit as st # type: ignore
import pandas as pd

EXPENSES_DF_PATH = "expenses-full-2022-2024.csv"

st.cache_data()
def load_data(path: str) -> pd.DataFrame:
    return pd.read_csv(path, sep=";")

def init_session_state():
    if "ss_picked_category" not in st.session_state:
        st.session_state.picked_category = "ALL"
        
    if "ss_agg_type" not in st.session_state:
        st.session_state.agg_type = "sum"

def main():
    url_of_data = st.text_input("URL of data to analyse", "local")
    if url_of_data == "local":
        df = load_data(EXPENSES_DF_PATH)
    else:
        try:
            if not url_of_data:
                url_of_data = "empty"
                raise ValueError()
            if not url_of_data.endswith("download"):
                url_of_data += "/download"
            df = load_data(url_of_data)
        except:
            st.error(f"Could not load data from {url_of_data}")
            return
    st.title(f"Expense analysis")
    
    # compute  "good" ordering of columns
    df_categories = df.groupby(["category_name"]).real_amount.sum().to_frame().sort_values("real_amount", ascending=False).reset_index()
    categories_pos = df_categories[df_categories.real_amount > 0].category_name.tolist()
    categories_neg = df_categories[df_categories.real_amount <= 0].category_name.tolist()[::-1]
    
    df_main_category = df.groupby(["main_category"]).real_amount.sum().to_frame().sort_values("real_amount", ascending=False).reset_index()
    main_category_pos = df_main_category[df_main_category.real_amount > 0].main_category.tolist()
    main_category_neg = df_main_category[df_main_category.real_amount <= 0].main_category.tolist()[::-1]

    # go ahead
    main_categories = ["ALL"] + sorted(df.main_category.unique().tolist())
    cc = st.columns([1, 6])
    with cc[0]:
        st.radio("Agg. type:", ["count", "sum"], key="ss_agg_type")
    with cc[1]:
        st.radio("Pick a main category", main_categories, key="ss_picked_category", horizontal=True)

    pivot_index = ["year", "month"]
    aggfunc = st.session_state.ss_agg_type
    _sign = 1 if aggfunc == "count" else -1
    if st.session_state.ss_picked_category == "ALL":
        by = "main categories"
        _df = df.copy()
        df_agg = _df.pivot_table(index=pivot_index, columns="main_category", values='real_amount', aggfunc=aggfunc).reset_index()
        df_agg["year_month"] = df_agg["month"].astype(str) + " - " + df_agg["year"].astype(str)
        df_agg = df_agg.set_index("year_month", drop=True)
        pos = main_category_pos
        neg = main_category_neg
    else:
        by = f"sub categories of {st.session_state.ss_picked_category}"
        _df = df.copy()[df.main_category == st.session_state.ss_picked_category]
        df_agg = _df.pivot_table(index=pivot_index, columns="category_name", values='real_amount', aggfunc=aggfunc).reset_index()
        df_agg["year_month"] = df_agg["month"].astype(str) + " - " + df_agg["year"].astype(str)
        df_agg = df_agg.set_index("year_month", drop=True)
        pos = [cat for cat in categories_pos if cat in df_agg]
        neg = [cat for cat in categories_neg if cat in df_agg]
    
    st.subheader(f"Incomes by {by} - comparison 2022 vs 2024 for months 04-08")
    st.bar_chart(df_agg, y=pos, use_container_width=True, stack=True, y_label="incomes")
    st.subheader(f"Expenses by {by} - comparison 2022 vs 2024 for months 04-08")
    st.bar_chart(_sign * df_agg, y=neg, use_container_width=True, stack=True, y_label="outcomes")
    
    st.subheader(f"In/out log for {by}")
    _df = _df[["date", "label", "main_category", "category_name", "shared", "proportion", "amount", "real_amount"]].set_index("date")
    _df["label"] = _df["label"].str.slice(0, 40)
    st.dataframe(_df)
    
    
    
if __name__ == '__main__':
    main()