import numpy as np
import streamlit as st  # type: ignore
import pandas as pd
from enum import Enum
import os

import altair as alt

EXPENSES_DF_PATH = "expenses-full-2022-2024.csv"
PIVOT_COL_NAME = "pivot_column"
DISPLAY_DATE_COL_NAME = "display_date"

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


class ShareType(MyEnum):
    PERSONAL = "perso"
    SHARED = "share"


class SharedExpenseAnalysis(MyEnum):
    INCLUDE = "include"
    EXCLUDE = "exclude"
    ONLY = "only"
    DIFFERENCIATE = "differenciate"


class TemporalDisplay(MyEnum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


def init_session_state():
    if "picked_category" not in st.session_state:
        st.session_state.picked_category = MotherCategory.ALL.value

    if "agg_type" not in st.session_state:
        st.session_state.agg_type = AggregationType.SUM.value

    if "include_shared_expenses" not in st.session_state:
        st.session_state.include_shared_expenses = SharedExpenseAnalysis.INCLUDE.value

    if "temporal_display" not in st.session_state:
        st.session_state.temporal_display = TemporalDisplay.MONTHLY.value

    if "data_location" not in st.session_state:
        st.session_state.data_location = None


@st.dialog("Select data source")
def ask_data_url():
    st.write(f"Copy paste URL/Path of data to analyse")
    if os.path.isfile(EXPENSES_DF_PATH):
        st.session_state.data_location = EXPENSES_DF_PATH
        st.rerun()
    else:
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

    cc = st.columns([1, 1, 1, 6])
    with cc[0]:
        st.radio("Agg. type", AggregationType.to_list(), key="agg_type")
    with cc[1]:
        st.radio(
            "Shared expenses",
            SharedExpenseAnalysis.to_list(),
            key="include_shared_expenses",
        )
    with cc[2]:
        st.radio("Temporal", TemporalDisplay.to_list(), key="temporal_display")
    with cc[-1]:
        st.radio(
            "Pick a main category",
            MotherCategory.to_list(),
            key="picked_category",
            horizontal=True,
        )

    aggfunc = st.session_state.agg_type

    st.subheader(f"Expenses by {st.session_state.picked_category} category - comparison 2022 vs 2024 for months 04-08")

    alt_chart = get_altair_chart_from_usecase(
        df.copy(),
        aggfunc,
        st.session_state.picked_category,
        st.session_state.include_shared_expenses,
        st.session_state.temporal_display,
    )

    _df = reshape_df_from_usecase(
        df.copy(),
        aggfunc,
        st.session_state.picked_category,
        st.session_state.include_shared_expenses,
        st.session_state.temporal_display,
    )

    # Chart
    st.altair_chart(alt_chart, use_container_width=True)

    st.write("---")
    # Savings/Expenses comparison
    cols = st.columns(2)

    if st.session_state.picked_category == "ALL":
        a = _df[_df.real_amount < 0].groupby(["year", PIVOT_COL_NAME]).agg({"real_amount": "sum"})
    else:
        a = _df[_df.real_amount < 0].groupby(["year", PIVOT_COL_NAME]).agg({"real_amount": "sum"})
    pivot_df = a.pivot_table(
        index=PIVOT_COL_NAME,
        columns="year",
        values="real_amount",
        aggfunc="sum",
        fill_value=0,
    )
    pivot_df = a.pivot_table(
        index=PIVOT_COL_NAME,
        columns="year",
        values="real_amount",
        aggfunc="sum",
        fill_value=0,
    )
    pivot_df.loc[:, "delta"] = pivot_df[2024] - pivot_df[2022]
    pivot_df.loc[:, "delta_pct"] = pivot_df["delta"] / np.abs(pivot_df[2022]) * 100

    pivot_df["color"] = np.where(pivot_df["delta"] < 0, "#eb4034", "#3496eb")
    pivot_df = pivot_df.sort_values("delta")
    with cols[0]:
        st.subheader("Savings 2024 wrt 2022 in €")
        st.bar_chart(pivot_df, y="delta", color="color")
    with cols[1]:
        st.subheader("Savings 2024 wrt 2022 in %")
        st.bar_chart(pivot_df, y="delta_pct", color="color")

    st.write("---")

    st.dataframe(
        _df[
            [
                "date",
                "week",
                "bank_name",
                "label",
                "amount",
                "shared",
                "real_amount",
                "main_category",
                "category_name",
                PIVOT_COL_NAME,
            ]
        ]
    )

    st.download_button("Download as csv", a.to_csv().encode("utf-8"), "selected_data.csv")


def get_y_min_max_from_usecase(df, aggfunc, category, include_shared_expenses, temporal_display) -> alt.Scale:

    if aggfunc == AggregationType.COUNT.value or category == MotherCategory.ALL.value:
        return alt.Undefined

    # prepare SELECT categ
    df = df[df.main_category == category]

    # prepare temporal granularity
    if temporal_display == TemporalDisplay.MONTHLY.value:
        df[DISPLAY_DATE_COL_NAME] = df["month"].astype(str) + " - " + df["year"].astype(str)
    else:
        df[DISPLAY_DATE_COL_NAME] = df["date"]

    agg_df = df.groupby(DISPLAY_DATE_COL_NAME).agg({"real_amount": "sum"})
    y_min = agg_df["real_amount"].min()
    y_max = agg_df["real_amount"].max()

    y_min = y_min - 0.1 * (y_max - y_min)
    y_max = y_max + 0.1 * (y_max - y_min)

    return alt.Scale(domain=[y_min, y_max])


def reshape_df_from_usecase(df, aggfunc, category, include_shared_expenses, temporal_display):
    pivot_col_content = []

    # prepare SELECT categ
    if category == MotherCategory.ALL.value:
        pivot_col_content.append("main_category")
    else:
        df = df[df.main_category == category]
        pivot_col_content.append("category_name")

    # prepare temporal granularity
    if temporal_display == TemporalDisplay.MONTHLY.value:
        df.loc[:, DISPLAY_DATE_COL_NAME] = df["month"].astype(str) + " - " + df["year"].astype(str)
    elif temporal_display == TemporalDisplay.WEEKLY.value:
        df.loc[:, DISPLAY_DATE_COL_NAME] = df["week"].astype(str) + " - " + df["year"].astype(str)
    else:
        df[DISPLAY_DATE_COL_NAME] = df["date"]

    # prepare shared expenses
    if include_shared_expenses == SharedExpenseAnalysis.INCLUDE.value:
        pass
    elif include_shared_expenses == SharedExpenseAnalysis.EXCLUDE.value:
        df = df[df.shared == ShareType.PERSONAL.value]
    elif include_shared_expenses == SharedExpenseAnalysis.ONLY.value:
        df = df[df.shared == ShareType.SHARED.value]
    elif SharedExpenseAnalysis.DIFFERENCIATE.value:
        pivot_col_content.append("shared")

    # reorder
    df = df.sort_values(["category_name"])

    # craft pivot column
    df.loc[:, PIVOT_COL_NAME] = df[pivot_col_content].astype(str).apply(lambda x: "-".join(x), axis=1)
    return df


def get_altair_chart_from_usecase(df, aggfunc, category, include_shared_expenses, temporal_display) -> alt.Chart:
    df = reshape_df_from_usecase(df, aggfunc, category, include_shared_expenses, temporal_display)
    scale = get_y_min_max_from_usecase(df, aggfunc, category, include_shared_expenses, temporal_display)

    alt_chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X(f"{DISPLAY_DATE_COL_NAME}:O", title="Month/Year"),
            y=alt.Y(
                f"{aggfunc}(real_amount):Q",
                scale=scale,
            ),
            color=PIVOT_COL_NAME,  # alt.Color(PIVOT_COL_NAME, sort=sort),
            order=PIVOT_COL_NAME,  # sort, #PIVOT_COL_NAME, #alt.Order(PIVOT_COL_NAME, sort=sort),
        )
    )
    return alt_chart


if __name__ == "__main__":
    main()
