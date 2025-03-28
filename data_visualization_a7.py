import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go

# Load dataset
dataset = {
    "Year": [1930, 1934, 1938, 1950, 1954, 1958, 1962, 1966, 1970, 1974, 1978,
             1982, 1986, 1990, 1994, 1998, 2002, 2006, 2010, 2014, 2018, 2022],
    "Winner": ["Uruguay", "Italy", "Italy", "Uruguay", "Germany", "Brazil", "Brazil", "England", "Brazil",
               "Germany", "Argentina", "Italy", "Argentina", "Germany", "Brazil", "France", "Brazil",
               "Italy", "Spain", "Germany", "France", "Argentina"],
    "Runner-up": ["Argentina", "Czechoslovakia", "Hungary", "Brazil", "Hungary", "Sweden", "Czechoslovakia",
                  "Germany", "Italy", "Netherlands", "Netherlands", "Germany", "Germany", "Argentina",
                  "Italy", "Brazil", "Germany", "France", "Netherlands", "Argentina", "Croatia", "France"]
}
df = pd.DataFrame(dataset)

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
    # Country Dropdown Section:
    html.Div([
        html.Label("Select a country:"),
        dcc.Dropdown(
            id="country-dropdown",
            options=[{"label": "All winners", "value": "All winners"}] +
                    [{"label": c, "value": c} for c in win_counts["Country"].unique()],
            value="All winners",  # Default to "All winners"
            placeholder="Select a country",
            style={"width": "250px", "margin": "0 auto"}
        ),
    ], style={"text-align": "center"}),
    
    # Div to display the number of wins for a selected country
    html.Div(id="win-output"),

    # Year Dropdown Section:
    html.Div([
        html.Label("Select a year:"),
        dcc.Dropdown(
            id="year-dropdown",
            options=[{"label": y, "value": y} for y in df["Year"].unique()],
            placeholder="Select a year",
            style={"width": "250px", "margin": "0 auto"}
        ),
    ], style={"text-align": "center"}),

    # Div to display the match result for a selected year
    html.Div(id="match-output"),
    
    # Displaying Graph
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
    # If a year is selected, show the match with discrete colors (navy for winner, grey for runner-up)
    if selected_year:
        match = df[df["Year"] == selected_year]
        if not match.empty:
            winner, runner_up = match.iloc[0][["Winner", "Runner-up"]]
            # Map country names for Plotly recognition
            winner_mapped = map_country(winner)
            runner_up_mapped = map_country(runner_up)
            # Get win counts (runner-ups may have 0 wins)
            winner_wins = win_counts.loc[win_counts["Country"] == winner, "Wins"].values[0] if winner in win_counts["Country"].values else 0
            runner_up_wins = win_counts.loc[win_counts["Country"] == runner_up, "Wins"].values[0] if runner_up in win_counts["Country"].values else 0
            
            # Create a discrete trace for the winner (navy blue)
            trace_winner = go.Choropleth(
                locations=[winner_mapped],
                locationmode="country names",
                z=[1],  # Dummy value
                text=[f"{winner} ({winner_wins} wins)"],
                hoverinfo="text",
                colorscale=[[0, "navy"], [1, "navy"]],
                marker_line_color="white",
                name="Winner",
                showscale=False
            )
            # Create a discrete trace for the runner-up (grey)
            trace_runnerup = go.Choropleth(
                locations=[runner_up_mapped],
                locationmode="country names",
                z=[1],  # Dummy value
                text=[f"{runner_up} ({runner_up_wins} wins)"],
                hoverinfo="text",
                colorscale=[[0, "grey"], [1, "grey"]],
                marker_line_color="white",
                name="Runner-up",
                showscale=False
            )
            fig = go.Figure(dataset=[trace_winner, trace_runnerup])
            fig.update_geos(scope="world")
            
            # Add a custom annotation acting as a legend for Winner/Runner-up,
            fig.add_annotation(
                x=0.95, y=0.7, xref="paper", yref="paper",
                text=("<b>Legend</b><br>"
                      "<span style='color:navy;'>&#9632;</span> Winner<br>"
                      "<span style='color:grey;'>&#9632;</span> Runner-up"),
                showarrow=False,
                align="left",
                bordercolor="black",
                borderwidth=1,
                bgcolor="rgba(255,255,255,0.7)",
                font=dict(size=12)
            )
        else:
            fig = go.Figure()
    
    # If a country is selected (but no year), display the number of wins on the map for that country
    elif selected_country != "All winners":
        filtered_data = win_counts[win_counts["Country"] == selected_country].copy()
        filtered_data["Result"] = "Winner"
        filtered_data["MappedCountry"] = filtered_data["Country"].apply(map_country)
        fig = px.choropleth(
            filtered_data,
            locations="MappedCountry",
            locationmode="country names",
            color="Wins",
            hover_data={"Country": True, "Wins": True},
            scope="world",
        )

        # Adding scattergeo for displaying number of wins only for the selected country
        scatter_data = filtered_data.copy()
        scatter_data["MappedCountry"] = scatter_data["Country"].apply(map_country)
        fig.add_trace(go.Scattergeo(
            locations=scatter_data["MappedCountry"],
            locationmode="country names",
            text=scatter_data["Wins"].astype(str),
            mode="text",
            showlegend=False,
            textfont=dict(size=10, color="black"),
            hoverinfo="none",
        ))
    
    # Default view: show all winners with colors based on number of wins and numbers on the map
    elif selected_country == "All winners":
        filtered_data = win_counts.copy()
        filtered_data["Result"] = "Winner"
        filtered_data["MappedCountry"] = filtered_data["Country"].apply(map_country)
        fig = px.choropleth(
            filtered_data,
            locations="MappedCountry",
            locationmode="country names",
            color="Wins",
            hover_data={"Country": True, "Wins": True},
            scope="world",
        )

        # Adding scattergeo for displaying number of wins for all countries
        scatter_data = filtered_data.copy()
        scatter_data["MappedCountry"] = scatter_data["Country"].apply(map_country)
        fig.add_trace(go.Scattergeo(
            locations=scatter_data["MappedCountry"],
            locationmode="country names",
            text=scatter_data["Wins"].astype(str),
            mode="text",
            showlegend=False,
            textfont=dict(size=10, color="black"),
            hoverinfo="none",
        ))
    
    # Update layout properties for consistent sizing and margins
    fig.update_layout(
        height=800,
        margin={"r": 0, "t": 50, "l": 0, "b": 0}
    )
    
    # Ensure fixed legend for non-year views (if needed)
    fig.update_layout(
        legend=dict(
            itemsizing='constant',
            title="Result",
            traceorder="normal",
            font=dict(size=12),
            orientation="v",
            x=0.2,
            y=0.5,
            bgcolor="rgba(255, 255, 255, 0.7)",
            bordercolor="black",
            borderwidth=1
        )
    )
    
    return fig


# Callback to display the win count for the selected country
@app.callback(
    Output("win-output", "children"),
    Input("country-dropdown", "value")
)
def display_wins(selected_country):
    if selected_country == "All winners":
        return ""
    if not selected_country:
        return ""
    wins = win_counts.loc[win_counts["Country"] == selected_country, "Wins"].values
    return f"{selected_country} has won the World Cup {wins[0]} times." if len(wins) > 0 else f"{selected_country} has never won the World Cup."

# Callback to display the match result (winner and runner-up) for the selected year
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

# Callback to disable year-dropdown if a country is selected
@app.callback(
    Output("year-dropdown", "disabled"),
    Input("country-dropdown", "value")
)
def disable_year_dropdown(selected_country):
    return False if selected_country is None else True

# Callback to disable country-dropdown if a year is selected
@app.callback(
    Output("country-dropdown", "disabled"),
    Input("year-dropdown", "value")
)
def disable_country_dropdown(selected_year):
    return False if selected_year is None else True

if __name__ == "__main__":
    app.run_server(debug=True, port=8090)


# In[ ]:




