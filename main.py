import requests
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go

# API ключ и URL
API_KEY = "b25b1d81e97defbfc78620fb023205fd"
BASE_URL = "http://api.openweathermap.org/data/2.5/forecast"

# Получение данных о погоде
def get_weather_data(city):
    url = BASE_URL
    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric",
        "lang": "ru"
    }
    response = requests.get(url, params=params)
    return response.json() if response.status_code == 200 else None

# Получение координат города
def get_city_coordinates(city):
    url = "http://api.openweathermap.org/geo/1.0/direct"
    params = {
        "q": city,
        "appid": API_KEY,
        "limit": 1
    }
    response = requests.get(url, params=params)
    data = response.json()
    return (data[0]["lat"], data[0]["lon"]) if data else (None, None)

# Инициализация Dash приложения
app = dash.Dash(__name__)
app.title = "Визуализация погоды"

app.layout = html.Div([
    html.H1("Визуализация погодных данных", style={"textAlign": "center", "marginBottom": "20px"}),

    # Поля для ввода маршрута
    html.Div([
        dcc.Input(id="start-city", type="text", placeholder="Начальная точка", style={"width": "300px"}),
        dcc.Textarea(id="mid-cities", placeholder="Промежуточные точки (по одной в строке)",
                     style={"width": "300px", "height": "100px"}),
        dcc.Input(id="end-city", type="text", placeholder="Конечная точка", style={"width": "300px"}),
        html.Button("Отправить", id="submit-button", n_clicks=0)
    ], style={"display": "flex", "justifyContent": "center", "marginBottom": "20px"}),

    # Dropdown для выбора параметра графика
    dcc.Dropdown(
        id='parameter-dropdown',
        options=[
            {'label': 'Температура', 'value': 'temperature'},
            {'label': 'Скорость ветра', 'value': 'wind_speed'},
            {'label': 'Вероятность осадков', 'value': 'precipitation'}
        ],
        value='temperature',  # Значение по умолчанию
        clearable=False,
        style={'width': '50%', 'margin': '0 auto'}
    ),

    # Ползунок по дням для выбора диапазона дат
    dcc.Slider(
        id='day-slider',
        min=1,
        max=7,
        value=3,
        marks={i: str(i) for i in range(1, 8)},
        step=1,
        tooltip={"always_visible": True, "placement": "bottom"}
    ),

    # Контейнер для графиков
    dcc.Graph(id="weather-graph"),
])

@app.callback(
    Output("weather-graph", "figure"),
    [Input("submit-button", "n_clicks"), Input("parameter-dropdown", "value"), Input("day-slider", "value")],
    [State("start-city", "value"), State("mid-cities", "value"), State("end-city", "value")]
)
def update_graph(n_clicks, selected_parameter, days_ahead, start_city, mid_cities, end_city):
    if n_clicks == 0:
        return go.Figure()  # Пустой график при первом запуске

    # Формируем список городов с учетом промежуточных точек (если они указаны)
    city_list = [start_city] + (
        [city.strip() for city in mid_cities.split("\n") if city.strip()] if mid_cities else []) + [end_city]

    all_data = {}
    for city in city_list:
        data = get_weather_data(city)
        if data:
            processed_data = [
                {
                    'time': entry["dt_txt"],
                    'temperature': entry["main"]["temp"],
                    'wind_speed': entry["wind"]["speed"],
                    'precipitation': entry.get("pop", 0) * 100,
                }
                for entry in data["list"][:days_ahead * 8]  # Получаем данные только на выбранное количество дней
            ]
            all_data[city] = processed_data

    fig = go.Figure()

    for city in all_data.keys():
        if selected_parameter == 'temperature':
            fig.add_trace(go.Scatter(
                x=[entry["time"] for entry in all_data[city]],
                y=[entry["temperature"] for entry in all_data[city]],
                mode='lines+markers',
                name=city
            ))
        elif selected_parameter == 'wind_speed':
            fig.add_trace(go.Scatter(
                x=[entry["time"] for entry in all_data[city]],
                y=[entry["wind_speed"] for entry in all_data[city]],
                mode='lines+markers',
                name=city
            ))
        elif selected_parameter == 'precipitation':
            fig.add_trace(go.Bar(
                x=[entry["time"] for entry in all_data[city]],
                y=[entry["precipitation"] for entry in all_data[city]],
                name=city
            ))

    fig.update_layout(title=f'{selected_parameter.capitalize()} по маршруту',
                      xaxis_title='Время',
                      yaxis_title=selected_parameter.capitalize(),
                      hovermode="x unified")

    return fig

if __name__ == "__main__":
    app.run(debug=True)
