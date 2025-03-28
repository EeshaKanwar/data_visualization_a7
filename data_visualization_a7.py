import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go

# Load dataset
data = {
    "Year": [1930, 1934, 1938, 1950, 1954, 1958, 1962, 1966, 1970, 1974, 1978,
             1982, 1986, 1990, 1994, 1998, 2002, 2006, 2010, 2014, 2018, 2022],
    "Winner": ["Uruguay", "Italy", "Italy", "Uruguay", "Germany", "Brazil", "Brazil", "England", "Brazil",
               "Germany", "Argentina", "Italy", "Argentina", "Germany", "Brazil", "France", "Brazil",
               "Italy", "Spain", "Germany", "France", "Argentina"],
    "Runner-up": ["Argentina", "Czechoslovakia", "Hungary", "Brazil", "Hungary", "Sweden", "Czechoslovakia",
                  "Germany", "Italy", "Netherlands", "Netherlands", "Germany", "Germany", "Argentina",
                  "Italy", "Brazil", "Germany", "France", "Netherlands", "Argentina", "Croatia", "France"]
}
df = pd.DataFrame(data)

# Count number of wins per country 
win_counts = df["Winner"].value_counts().reset_index()
win_counts.columns = ["Country", "Wins"]

# Mapping function for country names not recognized by Plotly
def map_country(country):
    mapping = {
        "Czechoslovakia": "Czechia",   # Map historical Czechoslovakia to modern Czechia
        "England": "United Kingdom"     # Map England to United Kingdom for Plotly's choropleth
    }
    return mapping.get(country, country)

# Create Dash app
app = dash.Dash()
server = app.server
app.layout = html.Div([
    html.H1("FIFA World Cup Winners Dashboard", style={"text-align": "center"}),
    
    # Country Dropdown
    html.Div([
        html.Label("Select a country:"),
        dcc.Dropdown(
            id="country-dropdown",
            options=[{"label": "All winners", "value": "All winners"}] +
                    [{"label": c, "value": c} for c in win_counts["Country"].unique()],
            value="All winners",
            style={"width": "250px", "margin": "0 auto"}
        ),
    ], style={"text-align": "center"}),
    
    html.Div(id="win-output"),

    # Year Dropdown
    html.Div([
        html.Label("Select a year:"),
        dcc.Dropdown(
            id="year-dropdown",
            options=[{"label": y, "value": y} for y in df["Year"].unique()],
            placeholder="Select a year",
            style={"width": "250px", "margin": "0 auto"}
        ),
    ], style={"text-align": "center"}),

    html.Div(id="match-output"),
    
    # Choropleth Map
    dcc.Graph(
        id="choropleth-map",
        config={"displayModeBar": False},
    ),
], style={"text-align": "center"})

# Main callback to update the choropleth map based on dropdown selections
@app.callback(
    Output("choropleth-map", "figure"),
    [Input("country-dropdown", "value"),
     Input("year-dropdown", "value")]
)
def update_map(selected_country, selected_year):
    fig = go.Figure()

    if selected_year:
        match = df[df["Year"] == selected_year]
        if not match.empty:
            winner, runner_up = match.iloc[0][["Winner", "Runner-up"]]
            winner_mapped, runner_up_mapped = map_country(winner), map_country(runner_up)
            winner_wins = win_counts.loc[win_counts["Country"] == winner, "Wins"].values[0] if winner in win_counts["Country"].values else 0
            runner_up_wins = win_counts.loc[win_counts["Country"] == runner_up, "Wins"].values[0] if runner_up in win_counts["Country"].values else 0

            # Winner Trace (Deep Purple)
            fig.add_trace(go.Choropleth(
                locations=[winner_mapped], locationmode="country names",
                z=[1], colorscale=[[0, "#6a0dad"], [1, "#6a0dad"]],
                text=[f"{winner} ({winner_wins} wins)"], hoverinfo="text",
                marker_line_color="white", name="Winner", showscale=False
            ))

            # Runner-up Trace (Grey)
            fig.add_trace(go.Choropleth(
                locations=[runner_up_mapped], locationmode="country names",
                z=[1], colorscale=[[0, "grey"], [1, "grey"]],
                text=[f"{runner_up} ({runner_up_wins} wins)"], hoverinfo="text",
                marker_line_color="white", name="Runner-up", showscale=False
            ))

            # **Legend for Winner & Runner-up**
            fig.add_annotation(
                x=0.95, y=0.7, xref="paper", yref="paper",
                text=("<b>Legend</b><br>"
                      "<span style='color:#6a0dad;'>&#9632;</span> Winner<br>"
                      "<span style='color:grey;'>&#9632;</span> Runner-up"),
                showarrow=False, align="left",
                bordercolor="black", borderwidth=1,
                bgcolor="rgba(255,255,255,0.7)", font=dict(size=12)
            )

    elif selected_country != "All winners":
        filtered_data = win_counts[win_counts["Country"] == selected_country].copy()
        filtered_data["MappedCountry"] = filtered_data["Country"].apply(map_country)
        
        # **Fix: Ensure z has a numeric value (even for single selections)**
        filtered_data["Wins"] = filtered_data["Wins"].astype(float)  

        fig.add_trace(go.Choropleth(
            locations=filtered_data["MappedCountry"], locationmode="country names",
            z=filtered_data["Wins"], colorscale="Viridis",
            text=filtered_data.apply(lambda row: f"{row['Country']} ({row['Wins']} wins)", axis=1),
            hoverinfo="text",
            marker_line_color="white", name="Wins"
        ))

        # **Overlay Numbers on Selected Country**
        fig.add_trace(go.Scattergeo(
            locations=filtered_data["MappedCountry"],
            locationmode="country names",
            text=filtered_data["Wins"].astype(str),
            mode="text", showlegend=False,
            textfont=dict(size=12, color="black"),
            hoverinfo="none",
        ))

    elif selected_country == "All winners":
        filtered_data = win_counts.copy()
        filtered_data["MappedCountry"] = filtered_data["Country"].apply(map_country)

        fig.add_trace(go.Choropleth(
            locations=filtered_data["MappedCountry"], locationmode="country names",
            z=filtered_data["Wins"], colorscale="Viridis",
            text=filtered_data.apply(lambda row: f"{row['Country']} ({row['Wins']} wins)", axis=1),
            hoverinfo="text",
            marker_line_color="white", name="Wins"
        ))

        # **Overlay Numbers for All Countries**
        fig.add_trace(go.Scattergeo(
            locations=filtered_data["MappedCountry"],
            locationmode="country names",
            text=filtered_data["Wins"].astype(str),
            mode="text", showlegend=False,
            textfont=dict(size=12, color="black"),
            hoverinfo="none",
        ))

    fig.update_layout(
        height=800, margin={"r": 0, "t": 50, "l": 0, "b": 0},
        geo=dict(showcoastlines=True, projection_type="natural earth")
    )

    return fig


# Callback to display the win count
@app.callback(
    Output("win-output", "children"),
    Input("country-dropdown", "value")
)
def display_wins(selected_country):
    if selected_country == "All winners" or not selected_country:
        return ""
    wins = win_counts.loc[win_counts["Country"] == selected_country, "Wins"].values
    return f"{selected_country} has won the World Cup {wins[0]} times." if len(wins) > 0 else f"{selected_country} has never won the World Cup."

# Callback to display match results
@app.callback(
    Output("match-output", "children"),
    Input("year-dropdown", "value")
)
def display_match(selected_year):
    if not selected_year:
        return ""
    match = df[df["Year"] == selected_year]
    if not match.empty:
        winner, runner_up = match.iloc[0][["Winner", "Runner-up"]]
        return f"In {selected_year}, {winner} won the World Cup, and {runner_up} was the runner-up."
    return "No data available for the selected year."

# Callback to disable year-dropdown when a country is selected
@app.callback(
    Output("year-dropdown", "disabled"),
    Input("country-dropdown", "value")
)
def disable_year_dropdown(selected_country):
    return False if selected_country is None else True

# Callback to disable country-dropdown when a year is selected
@app.callback(
    Output("country-dropdown", "disabled"),
    Input("year-dropdown", "value")
)
def disable_country_dropdown(selected_year):
    return False if selected_year is None else True

if __name__ == "__main__":
    app.run_server(debug=True, port=8090)
