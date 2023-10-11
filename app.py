# -*- coding: utf-8 -*-

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

from dash import Dash, html, dash_table, dcc, Output, Input, callback
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import random
from urllib.request import urlopen
import json

# Initialize the app - incorporate css
# external_stylesheets = ['./style.css']

app = Dash(__name__)

app.title = "Airbnb listings dashboard"
server = app.server
app.config.suppress_callback_exceptions = True

listings = pd.read_csv("listings.csv")
number_of_listings = len(listings)
neighbourhoods = listings["neighbourhood_cleansed"].unique()
content_font_size = "13px"

# percentage of guests who DON'T leave a review
guests_not_leaving_review = 0.65

header_question_text = (
    "How is Airbnb really being used in and affecting your neighbourhoods?"
)

room_type_text = """Airbnb hosts can list entire homes/apartments, private or
                    shared rooms. Depending on the room type, availability, and
                    activity, an airbnb listing could be more like a hotel,
                    disruptive for neighbours, taking away housing, and illegal."""

activity_text_1 = "Airbnb guests may leave a review after their stay, and these can be used as an indicator of airbnb activity.\n"
activity_text_2 = """The minimum stay, price and number of reviews have been used to estimate the occupancy rate, the number of
                    nights per year and the income per month for each listing."""
activity_text_3 = "How does the income from Airbnb compare to a long-term lease?"
activity_text_4 = "Do the number of nights booked per year make it impossible for a listing to be used for residential housing?"
activity_text_5 = "And what is renting to a tourist full-time rather than a resident doing to our neighbourhoods and cities?"

# Functions


def header():
    return html.Div(
        [
            html.H4("Airbnb listings dashboard", className="title"),
            html.H5("Adding data to the debate", className="subtitle"),
        ],
    )


def make_hist(df):
    df_entire_home = df[df["room_type"] == "Entire home/apt"].room_type
    df_private_room = df[df["room_type"] == "Private room"].room_type
    df_shared_room = df[df["room_type"] == "Shared room"].room_type
    fig = go.Figure()
    fig.add_trace(
        go.Histogram(y=df_shared_room, marker_color="blue", name="Shared room")
    )
    fig.add_trace(
        go.Histogram(y=df_private_room, marker_color="green", name="Private room")
    )
    fig.add_trace(
        go.Histogram(y=df_entire_home, marker_color="red", name="Entire home/apt")
    )
    fig.update_yaxes(visible=False, showticklabels=False)
    fig.update_traces(showlegend=False)

    return fig


def make_hovertemplate(customdata):
    return """<b>Apartment: %{customdata[0]}</b><br><b>Host name: </b><b>%{customdata[1]}</b><br><b>Host Since:
            </b>%{customdata[2]}<br><b>Price: </b>%{customdata[3]} / night<br><b>Person to accommodate: </b>%{customdata[4]}
            <br><b>Yearly Availability: </b>%{customdata[5]} days/year"""


def make_mapchart(df):
    customdata = list(
        zip(
            df["name"],
            df["host_name"],
            df["host_since"],
            df["price"],
            df["accommodates"],
            round(df["availability_365"] / 365 * 100, 1),
        )
    )

    df_entire_home = df[df["room_type"] == "Entire home/apt"]
    df_private_room = df[df["room_type"] == "Private room"]
    df_shared_room = df[df["room_type"] == "Shared room"]

    data = [
        dict(
            type="scattermapbox",
            lat=df_entire_home["latitude"],
            lon=df_entire_home["longitude"],
            marker={"color": "red"},
            customdata=customdata,
            name="Entire home",
            hovertemplate=make_hovertemplate(customdata),
        ),
        dict(
            type="scattermapbox",
            lat=df_private_room["latitude"],
            lon=df_private_room["longitude"],
            marker={"color": "green"},
            customdata=customdata,
            name="Private room",
            hovertemplate=make_hovertemplate(customdata),
        ),
        dict(
            type="scattermapbox",
            lat=df_shared_room["latitude"],
            lon=df_shared_room["longitude"],
            marker={"color": "blue"},
            customdata=customdata,
            name="Shared room",
            hovertemplate=make_hovertemplate(customdata),
        ),
    ]
    layout = dict(
        mapbox=dict(
            style="open-street-map",
            uirevision=True,
            zoom=13,
            center=dict(
                lon=df["longitude"].mean(),
                lat=df["latitude"].mean(),
            ),
        ),
        margin=dict(l=10, t=10, b=10, r=10),
        height=900,
        showlegend=False,
        hovermode="closest",
    )
    figure = {"data": data, "layout": layout}
    return figure


def room_type():
    return (
        html.P(header_question_text, style={"font-weight": "bold"}),
        html.H5("Room Type"),
        html.Hr(),
        html.Div(
            [
                html.P(
                    room_type_text,
                    style={"width": "100px", "font-size": content_font_size},
                ),
                dcc.Graph(
                    id="hist",
                    figure=make_hist(listings),
                    config={"displayModeBar": False},
                    style={"width": "60%"},
                ),
                html.Div(
                    [
                        html.H3(id="ent_home_perc"),
                        html.P("entire homes/apartments"),
                        html.P(id="price_night", style={"font-weight": "bold"}),
                        html.P("price/night"),
                    ],
                    style={
                        "text-align": "right",
                        "padding": "5px",
                        "font-size": content_font_size,
                    },
                ),
            ],
            className="sidePanelContent",
        ),
    )


def activity():
    return (
        html.H5("Activity"),
        html.Hr(),
        html.Div(
            [
                html.Div(
                    [
                        html.P(activity_text_1),
                        html.P(activity_text_2),
                        html.P(activity_text_3),
                        html.P(activity_text_4),
                        html.P(activity_text_5),
                    ],
                    style={"width": "60%", "font-size": content_font_size},
                ),
                html.Div(
                    [
                        html.H3(id="est_nights_year"),
                        html.P("estimated nights/year"),
                        html.P(
                            id="reviews_listings_month", style={"font-weight": "bold"}
                        ),
                        html.P("reviews/listing/month"),
                        html.P(id="number_of_reviews", style={"font-weight": "bold"}),
                        html.P("reviews"),
                        html.P(id="est_occupancy", style={"font-weight": "bold"}),
                        html.P("estimated occupancy"),
                        html.P(
                            id="estimated_income_month", style={"font-weight": "bold"}
                        ),
                        html.P("estimated income/month"),
                    ],
                    style={"padding": "5px", "font-size": content_font_size},
                ),
            ],
            className="sidePanelContent",
        ),
    )


def side_panel():
    return html.Div(
        [
            html.Div(
                children=[
                    html.H2("Venice"),
                    html.P("filter by"),
                    html.Div(
                        [
                            dcc.Dropdown(
                                id="nbh_dropdown",
                                options=[
                                    {"label": nbh, "value": nbh}
                                    for nbh in neighbourhoods
                                ],
                                className="nbhDropdown",
                            ),
                            html.Div(
                                [
                                    html.H3(id="num_listings"),
                                    html.P(
                                        "out of "
                                        + str(number_of_listings)
                                        + " listings"
                                    ),
                                    html.P(id="perc_listings"),
                                ],
                                style={"text-align": "right"},
                            ),
                        ],
                        className="sidePanelContent",
                    ),
                ],
                className="contentHeader",
            ),
            html.P(header_question_text, style={"font-weight": "bold"}),
            html.H5("Room Type"),
            html.Hr(),
            html.Div(
                [
                    html.P(
                        room_type_text,
                        style={"width": "100px", "font-size": content_font_size},
                    ),
                    dcc.Graph(
                        id="hist",
                        figure=make_hist(listings),
                        config={"displayModeBar": False},
                        style={"width": "60%"},
                    ),
                    html.Div(
                        [
                            html.H3(id="ent_home_perc"),
                            html.P("entire homes/apartments"),
                            html.P(id="price_night", style={"font-weight": "bold"}),
                            html.P("price/night"),
                        ],
                        style={
                            "text-align": "right",
                            "padding": "5px",
                            "font-size": content_font_size,
                        },
                    ),
                ],
                className="sidePanelContent",
            ),
            html.H5("Activity"),
            html.Hr(),
            html.Div(
                [
                    html.Div(
                        [
                            html.P(activity_text_1),
                            html.P(activity_text_2),
                            html.P(activity_text_3),
                            html.P(activity_text_4),
                            html.P(activity_text_5),
                        ],
                        style={"width": "60%", "font-size": content_font_size},
                    ),
                    html.Div(
                        [
                            html.H3(id="est_nights_year"),
                            html.P("estimated nights/year"),
                            html.P(
                                id="reviews_listings_month",
                                style={"font-weight": "bold"},
                            ),
                            html.P("reviews/listing/month"),
                            html.P(
                                id="number_of_reviews", style={"font-weight": "bold"}
                            ),
                            html.P("reviews"),
                            html.P(id="est_occupancy", style={"font-weight": "bold"}),
                            html.P("estimated occupancy"),
                            html.P(
                                id="estimated_income_month",
                                style={"font-weight": "bold"},
                            ),
                            html.P("estimated income/month"),
                        ],
                        style={"padding": "5px", "font-size": content_font_size},
                    ),
                ],
                className="sidePanelContent",
            ),
        ],
        className="sidePanel",
    )


@callback(
    Output("map", "figure"),
    Output("hist", "figure"),
    Output("est_nights_year", "children"),
    Output("est_occupancy", "children"),
    Output("estimated_income_month", "children"),
    Output("price_night", "children"),
    Output("reviews_listings_month", "children"),
    Output("number_of_reviews", "children"),
    Output("num_listings", "children"),
    Output("perc_listings", "children"),
    Output("ent_home_perc", "children"),
    Input(component_id="nbh_dropdown", component_property="value"),
)
def update_num_listings(nbh_cleansed):
    if nbh_cleansed is not None:
        dff = listings[listings["neighbourhood_cleansed"] == nbh_cleansed]
    else:
        dff = listings
    mapchart = make_mapchart(dff)
    hist = make_hist(dff)
    price_night = pd.to_numeric(
        dff["price"].str.replace("$", "").str.replace(",", "").str.rstrip(".00")
    ).mean()
    est_nights_year = (
        (dff["minimum_nights_avg_ntm"] * dff["reviews_per_month"]).dropna().mean()
        * 12
        * (1 / (1 - guests_not_leaving_review))
    )
    est_occupancy = est_nights_year / 365
    estimated_income_month = price_night * est_nights_year / 12
    return (
        mapchart,
        hist,
        "{:0.0f}".format(est_nights_year),
        "{:0.0%}".format(est_occupancy),
        "$" + "{:0.2f}".format(estimated_income_month),
        "$" + "{:0.2f}".format(price_night),
        "{:0.2f}".format(dff["reviews_per_month"].dropna().mean()),
        "{:0.0f}".format(dff["number_of_reviews"].sum()),
        len(dff),
        "(" + "{:.0%}".format(len(dff) / len(listings)) + ")",
        "{:.0%}".format(len(dff[dff["room_type"] == "Entire home/apt"]) / len(dff)),
    )


def body():
    return html.Div(
        children=[
            dcc.Graph(id="map", figure=make_mapchart(listings)),
            side_panel(),
        ],
        className="columns",
    )


# Dash App Layout
app.layout = html.Div(
    children=[
        header(),
        body(),
    ]
)


if __name__ == "__main__":
    app.run(debug=True)
