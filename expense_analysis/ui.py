import streamlit as st # type: ignore
import pandas as pd
from enum import Enum

EXPENSES_DF_PATH = "expenses-full-2022-2024.csv"

st.set_page_config(layout="wide")

st.cache_data()
def load_data(path: str) -> pd.DataFrame:
    path = path.strip()
    if path.startswith("http") and not path.endswith("download"):
        path += "/download"
    return pd.read_csv(path, sep=";")

class MyEnum(Enum):
    @classmethod
    def to_list(cls) -> list:
        return [e.value for e in cls]

class MotherCategory(MyEnum):
    ALL = "ALL"
    APPARTMENT = "appartment"
    BANK = "bank"
    CAR = "car"
    CHILLOUT = "chillOut"
    CULTURE = "culture"
    DAILYLIFE = "dailyLife"
    GIFTS = "gifts"
    HEALTH = "health"
    HOLIDAY = "holiday"
    INCOME = "income"
    KIDS = "kids"
    PETS = "pets"
    PRO = "pro"
    SPORT = "sport"
    TRANSPORT = "transport"
    TRAVEL = "travel"
    
class AggregationType(MyEnum):
    COUNT = "count"
    SUM = "sum"
    
class SharedExpense(MyEnum):
    YES = "yes"
    NO = "no"
    COMPARE = "compare"
    

def init_session_state():
    if "picked_category" not in st.session_state:
        st.session_state.picked_category = MotherCategory.ALL.value
        
    if "agg_type" not in st.session_state:
        st.session_state.agg_type = AggregationType.SUM.value
        
    if "sharing_type" not in st.session_state:
        st.session_state.sharing_type = SharedExpense.YES.value
        
    if "data_location" not in st.session_state:
        st.session_state.data_location = None

@st.dialog("Select data source")
def ask_data_url():
    st.write(f"Copy paste URL/Path of data to analyse")
    data_location = st.text_input("available at:")
    if st.button("Submit"):
        st.session_state.data_location = data_location
        st.rerun()

def main():
    init_session_state()
    if st.session_state.data_location is None:
        ask_data_url()
    
    if st.session_state.data_location is None:
        st.write("No data to analyse")
    else:
        show_analysis()
        
def show_analysis():
    df = load_data(st.session_state.data_location)
    st.title(f"Expense analysis")
    
    # compute  "good" ordering of columns
    df_categories = df.groupby(["category_name"]).real_amount.sum().to_frame().sort_values("real_amount", ascending=False).reset_index()
    categories_pos = df_categories[df_categories.real_amount > 0].category_name.tolist()
    categories_neg = df_categories[df_categories.real_amount <= 0].category_name.tolist()[::-1]
    
    df_main_category = df.groupby(["main_category"]).real_amount.sum().to_frame().sort_values("real_amount", ascending=False).reset_index()
    main_category_pos = df_main_category[df_main_category.real_amount > 0].main_category.tolist()
    main_category_neg = df_main_category[df_main_category.real_amount <= 0].main_category.tolist()[::-1]

    # go ahead
    cc = st.columns([1, 1, 6])
    with cc[0]:
        st.radio("Agg. type", AggregationType.to_list(), key="agg_type")
    with cc[1]:
        st.radio("Shared expenses", SharedExpense.to_list(), key="sharing_type")
    with cc[2]:
        st.radio("Pick a main category", MotherCategory.to_list(), key="picked_category", horizontal=True)

    # df_agg = get_aggregated_data(df, st.session_state.agg_type, st.session_state.sharing_type, st.session_state.picked_category)
    pivot_index = ["year", "month"]
    aggfunc = st.session_state.agg_type
    _sign = 1 if aggfunc == "count" else -1
    if st.session_state.picked_category == "ALL":
        by = "main categories"
        _df = df.copy()
        df_agg = _df.pivot_table(index=pivot_index, columns="main_category", values='real_amount', aggfunc=aggfunc).reset_index()
        df_agg["year_month"] = df_agg["month"].astype(str) + " - " + df_agg["year"].astype(str)
        df_agg = df_agg.set_index("year_month", drop=True)
        pos = main_category_pos
        neg = main_category_neg
    else:
        by = f"sub categories of {st.session_state.picked_category}"
        _df = df.copy()[df.main_category == st.session_state.picked_category]
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