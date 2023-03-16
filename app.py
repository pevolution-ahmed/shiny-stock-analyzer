import numpy as np
import pandas as pd
import datetime as dt
from plotly import express as px
import plotly.graph_objects as go
from pathlib import Path
import matplotlib.pyplot as plt

from shinywidgets import (
    output_widget, render_widget
)
from shiny import (
    App, ui, render, reactive, Session, req
)
from yahooquery import Ticker

# import requests_cache
# session = requests_cache.CachedSession('yfinance.cache')
# session.headers['User-agent'] = 'stock_analyzer/1.0'


TITLE = "Finantial Stock Analyzer"

# Data INGEST Placholders
symbol = "MSFT"
period = "5y"
window_mavg_short = 30
window_mavg_long = 90


page_dependencies = ui.tags.head(
    ui.tags.link(rel="stylesheet", type="text/css", href="style.css"),
    ui.tags.script(src="https://unpkg.com/@mojs/core"),
    ui.tags.script(src="https://cdn.jsdelivr.net/npm/@mojs/core"),
    ui.tags.script(src="preloader.js"),

)



def get_daily_return_to_df(df):
    return (df['close'] / df['close'].shift(1)) - 1


def my_card(title, value, width=12, bg_color="bg-info", text_color="text-white"):
    """
        Function to generate a bootstrap 5 card
    """
    card_ui = ui.div(
        ui.div(
            ui.div(
                ui.div(ui.h6(title), class_="card-title"),
                ui.div(value, class_="card-text"),
                class_="card-body flex-fill"
            ),
            class_=f"card {text_color} {bg_color}",
            style="flex-grow:1;margin:5px;"
        ),
        class_=f" d-flex"
    )

    return card_ui


app_ui = ui.page_fluid(
    ui.div(id="js-constrain",class_="contrain"),
    ui.page_navbar(
        ui.nav(
            "Stock Technical Analysis",
            ui.layout_sidebar(
                sidebar=ui.panel_sidebar(
                    ui.h2("Select a stock"),
                    ui.input_selectize(
                        "stock_symbol",
                        "Stock Symbol",
                        ['AAPL', 'GOOG', 'MSFT',],
                        selected='MSFT',
                        multiple=False
                    ),
                    ui.output_ui("stock_info_ui"),
                    width=3,
                    class_="go lead",
                ),
                main=ui.panel_main(
                    ui.row(
                        ui.panel_well(
                            ui.div(
                                ui.div(ui.div("What is Ichimoku?"),class_="display-6",style="color:#769cf5"),
                                ui.div("The Ichimoku Cloud is a collection of technical indicators that show support and resistance levels, as well as momentum and trend direction. It does this by taking multiple averages and plotting them on a chart. It also uses these figures to compute a “cloud” that attempts to forecast where the price may find support or resistance in the future.",class_="lead",style="color:white"),
                                ui.a("Check out this short video on How to Use Ichimoku 📉",href="https://www.youtube.com/watch?v=mr4n3M9bexY&ab_channel=SwitchStats", target_="blank")
                            ),
                            ui.hr(),
                            ui.div(
                                output_widget(
                                    "stock_Ichimoku_widget", width="auto", height="auto"),
                                class_="card oo lead"
                            )
                        )
                    ),
                    ui.hr(),
                    ui.row(
                        ui.column(8,
                                  ui.div(
                                      output_widget(
                                          "stock_daily_return_chart_widget", width="auto", height="auto"),
                                      class_="card oo lead"
                                  ),
                                  ),
                        ui.output_ui("stock_recommends_ui",class_="col-sm-4 lead"),
                        class_="oo"),
                    ui.row(
                        ui.panel_well(
                            ui.div(
                                output_widget(
                                    "stock_boll_bands_widget", width="auto", height="auto"),
                                class_="card oo"
                            )
                        ),
                    )

                )
            )
        ),
        title=ui.tags.div(
            ui.img(src="shiny-solo.svg", height="50px", style="margin:5px;"),
            style="display:flex;-webkit-filter:drop-shadow(2px 2px 2px #222);",
        ),
        bg="#769cf5",
        inverse=True,
        header=page_dependencies,
    )

)


def add_cum_return_to_df(df):
    df['cum_return'] = (1 + df['daily_return']).cumprod()
    return df


def add_bollinger_bands(df):
    df['middle_band'] = df['close'].rolling(window=20).mean()
    df['upper_band'] = df['middle_band'] + 1.96 * \
        df['close'].rolling(window=20).std()
    df['lower_band'] = df['middle_band'] - 1.96 * \
        df['close'].rolling(window=20).std()
    return df


def add_Ichimoku(df):
    # Conversion
    hi_val = df['high'].rolling(window=9).max()
    low_val = df['low'].rolling(window=9).min()
    df['Conversion'] = (hi_val + low_val) / 2

    # Baseline
    hi_val2 = df['high'].rolling(window=26).max()
    low_val2 = df['low'].rolling(window=26).min()
    df['Baseline'] = (hi_val2 + low_val2) / 2

    # Spans
    df['SpanA'] = ((df['Conversion'] + df['Baseline']) / 2).shift(26)
    hi_val3 = df['high'].rolling(window=52).max()
    low_val3 = df['low'].rolling(window=52).min()
    df['SpanB'] = ((hi_val3 + low_val3) / 2).shift(26)
    df['Lagging'] = df['close'].shift(-26)

    return df


def plot_with_boll_bands(df):
    df = add_bollinger_bands(df)

    fig = go.Figure()

    candle = go.Candlestick(x=df.index, open=df['open'],
                            high=df['high'], low=df['low'],
                            close=df['close'], name="Candlestick")

    upper_line = go.Scatter(x=df.index, y=df['upper_band'],
                            line=dict(color='#ff006e',
                                      width=1), name="Upper Band")

    mid_line = go.Scatter(x=df.index, y=df['middle_band'],
                          line=dict(color='#fcbf49',
                                    width=0.7), name="Middle Band")

    lower_line = go.Scatter(x=df.index, y=df['lower_band'],
                            line=dict(color='#7678ed',
                                      width=1), name="Lower Band")

    fig.add_trace(candle)
    fig.add_trace(upper_line)
    fig.add_trace(mid_line)
    fig.add_trace(lower_line)

    fig.update_xaxes(title="Date", rangeslider_visible=True)
    fig.update_yaxes(title="Price")

    # USED FOR NON-DAILY DATA : Get rid of empty dates and market closed
    # fig.update_layout(title=ticker + " Bollinger Bands",
    # height=1200, width=1800,
    #               showlegend=True,
    #               xaxis_rangebreaks=[
    #         dict(bounds=["sat", "mon"]),
    #         dict(bounds=[16, 9.5], pattern="hour"),
    #         dict(values=["2021-12-25", "2022-01-01"])
    #     ])

    fig.update_layout(
        title="Bollinger Bands",
        plot_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        paper_bgcolor='rgba(0,0,0,0)',
        legend_title_text='',
        showlegend=True
    )
    return fig

# Used to generate the red and green fill for the Ichimoku cloud


def get_fill_color(label):
    if label >= 1:
        return 'rgba(0,250,0,0.4)'
    else:
        return 'rgba(250,0,0,0.4)'


def get_Ichimoku(df):
    df = add_Ichimoku(df)
    candle = go.Candlestick(x=df.index, open=df['open'],
                            high=df['high'], low=df["low"], close=df['close'], name="Candlestick")

    df1 = df.copy()
    fig = go.Figure()
    df['label'] = np.where(df['SpanA'] > df['SpanB'], 1, 0)
    df['group'] = df['label'].ne(df['label'].shift()).cumsum()

    df = df.groupby('group')

    dfs = []
    for name, data in df:
        dfs.append(data)

    for df in dfs:
        fig.add_traces(go.Scatter(x=df.index, y=df.SpanA,
                                  line=dict(color='rgba(0,0,0,0)')))

        fig.add_traces(go.Scatter(x=df.index, y=df.SpanB,
                                  line=dict(color='rgba(0,0,0,0)'),
                                  fill='tonexty',
                                  fillcolor=get_fill_color(df['label'].iloc[0])))

    baseline = go.Scatter(x=df1.index, y=df1['Baseline'],
                          line=dict(color='pink', width=2), name="Baseline")

    conversion = go.Scatter(x=df1.index, y=df1['Conversion'],
                            line=dict(color='aqua', width=1), name="Conversion")

    lagging = go.Scatter(x=df1.index, y=df1['Lagging'],
                         line=dict(color='purple', width=2), name="Lagging")

    span_a = go.Scatter(x=df1.index, y=df1['SpanA'],
                        line=dict(color='green', width=2, dash='dot'), name="Span A")

    span_b = go.Scatter(x=df1.index, y=df1['SpanB'],
                        line=dict(color='red', width=1, dash='dot'), name="Span B")

    fig.add_trace(candle)
    fig.add_trace(baseline)
    fig.add_trace(conversion)
    fig.add_trace(lagging)
    fig.add_trace(span_a)
    fig.add_trace(span_b)

    fig.update_layout(
        title="Ichimoku Leading Indicator",
        plot_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        paper_bgcolor='rgba(0,0,0,0)',
        legend_title_text='',
        showlegend=True)

    return fig


def make_plotly_daily_returns(stock_history):
    """
        Drop-in Replacement for plotly code
    """
    stock_df = stock_history[['close', 'date']].reset_index()
    stock_df['daily_return'] = get_daily_return_to_df(stock_df)
    px.data.stocks(indexed=True)-1
    fig = px.line(
        data_frame=stock_df,
        x='date',
        y='daily_return',
        color_discrete_map={
            "daily_return": "#ffffff",
        },
        title="Daily Returns"
    ).update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        paper_bgcolor='rgba(0,0,0,0)',
        legend_title_text=symbol+" indicators"
    ).update_yaxes(
        title="Share Price",
        tickprefix="$",
        gridcolor='#2c3e50'
    ).update_xaxes(
        title="Date",
        gridcolor='#2c3e50'
    )
    # fig = px.bar(
    #     data_frame=stock_df,
    #     color_discrete_map= {
    #         "daily_return":"#FFFFFF",
    #     },
    #     title= None
    # ).update_layout(
    #     plot_bgcolor = 'rgba(0,0,0,0)',
    #     font_color='#90bde5',
    #     paper_bgcolor = 'rgba(0,0,0,0)',
    #     legend_title_text=symbol+" indicators"
    # ).update_yaxes(
    #     title = "Share Price",
    #     tickprefix="$",
    #     gridcolor='#2c3e50'
    # ).update_xaxes(
    #     title="Date",
    #     gridcolor='#2c3e50'
    # )
    return fig


def make_plotly_chart(stock_history, window_mavg_short=30, window_mavg_long=90):
    """
        Drop-in Replacement for plotly code
    """
    stock_df = stock_history[['close']].reset_index()
    stock_df['mavg_short'] = stock_df['close'] \
        .rolling(window=window_mavg_short) \
        .mean()
    stock_df['mavg_long'] = stock_df['close'] \
        .rolling(window=window_mavg_long) \
        .mean()
    px.data.stocks(indexed=True)-1

    fig = px.line(
        data_frame=stock_df.set_index('date'),
        color_discrete_map={
            "close": "#e06666",
            "mavg_short": "#0d6efd",
            "mavg_long": "#0dcaf0"
        },
        title=None
    ).update_layout(
        title="Short-to-Long Moving Averages",
        plot_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        paper_bgcolor='rgba(0,0,0,0)',
        legend_title_text=''
    ).update_yaxes(
        title="Share Price",
        tickprefix="$",
        gridcolor='#2c3e50'
    ).update_xaxes(
        title="Date",
        gridcolor='#2c3e50'
    )
    return fig


def server(input, output, session: Session):

    @reactive.Calc
    def stock():
        return Ticker(str(input.stock_symbol()))

    @reactive.Calc
    def stock_financial():
        return Ticker(str(input.stock_symbol())).financial_data[str(input.stock_symbol())]

    @reactive.Calc
    def stock_profile():
        return Ticker(str(input.stock_symbol())).asset_profile[str(input.stock_symbol())]

    @output
    @render.text
    def txt():
        return f"You Selected: {str(input.stock_symbol())}"

    @output
    @render.ui
    def stock_recommends_ui():
        stock_info = stock_financial()

        app_ui = ui.column(12,
                          ui.div("Recommendation Ratios",class_="lead"),
                          my_card("Number Of Analyst Opinions", "{:0,.1%}".format(
                              stock_info['numberOfAnalystOpinions']), bg_color="bg-dark"),
                          my_card("Recommendation Key", "{rk}".format(
                              rk=stock_info['recommendationKey']), bg_color="bg-dark"),
                          my_card("Recommendation Mean", "{:0,.2f}".format(
                              stock_info['recommendationMean']), bg_color="bg-dark")
                          )
        return app_ui

    @output
    @render.ui
    def stock_info_ui():
        stock_info = stock_financial()

        stock_company_info = stock_profile()
        app_ui = ui.row(
            # Company Info
            ui.div("Company Information",class_="lead"),
            my_card(
                "Industry", stock_company_info['industry'], bg_color="bg-dark"),
            my_card("Fulltime Employees", "{:0,.0f}".format(
                stock_company_info['fullTimeEmployees']), bg_color="bg-dark"),
            my_card("Website", ui.a(
                stock_company_info['website'], href=stock_company_info['website'], target_="blank"), bg_color="bg-dark"),

            ui.hr(),

            # Finantial Ratios
            ui.div("Financial Ratios",class_="lead"),

            my_card("Profit Margin", "{:0,.1%}".format(
                stock_info['profitMargins']), bg_color="bg-dark"),
            my_card("Revenue Growth", "{:0,.1%}".format(
                stock_info['revenueGrowth']), bg_color="bg-dark"),
            my_card("Current Ratio", "{:0,.2f}".format(
                stock_info['currentRatio']), bg_color="bg-dark"),

            ui.hr(),

            # Financial Operations
            ui.div("Financial Operations",class_="lead"),
            my_card("Total Revenue", "${:0,.0f}".format(
                stock_info['totalRevenue']), bg_color="bg-dark"),
            my_card("EBITDA", "${:0,.0f}".format(
                stock_info['ebitda']), bg_color="bg-dark"),
            my_card("Operating Cash Flow", "${:0,.0f}".format(
                stock_info['operatingCashflow']), bg_color="bg-dark"),

        )
        return app_ui

    # # Build Stock Chart
    @output
    @render_widget
    def stock_chart_widget():
        stock_history = stock().history(period=period).reset_index()
        stock_history.date = stock_history.date.astype(
            'datetime64[ns, America/New_York]')
        fig = make_plotly_chart(
            stock_history, window_mavg_short, window_mavg_long)
        return go.FigureWidget(fig)

    @output
    @render_widget
    def stock_daily_return_chart_widget():
        stock_history = stock().history(period=period).reset_index()
        stock_history.date = stock_history.date.astype(
            'datetime64[ns, America/New_York]')
        fig = make_plotly_daily_returns(stock_history)
        return go.FigureWidget(fig)

    @output
    @render_widget
    def stock_boll_bands_widget():
        stock_history = stock().history(period=period).reset_index()
        stock_history.date = stock_history.date.astype(
            'datetime64[ns, America/New_York]')
        fig = plot_with_boll_bands(stock_history)
        return go.FigureWidget(fig)

    @output
    @render_widget
    def stock_Ichimoku_widget():
        stock_history = stock().history(period=period).reset_index()
        stock_history.date = stock_history.date.astype(
            'datetime64[ns, America/New_York]')
        fig = get_Ichimoku(stock_history)
        return go.FigureWidget(fig)

    # Build Income Statement
    @output
    @render.table
    def income_statement_table():
        return (
            stock().stock_incomestmt.reset_index()
        )


www_dir = Path(__file__).parent / "front-end"
print(www_dir)

app = App(app_ui, server, static_assets=www_dir)
