from flask import Flask, render_template, request
import requests
import datetime
from multipledispatch import dispatch

app = Flask(__name__)
app.secret_key = 'your_secret_key'

API_KEY = '....'
BASE_URL = 'http://api.openweathermap.org/data/2.5/weather'
FORECAST_URL = 'http://api.openweathermap.org/data/2.5/forecast'


@app.route('/')
def home():
    return render_template('index.html', today_at_times={}, forecast_list=[], error=None, health_alerts=[], weather_recommendations=[])


def get_weather_emoji(weather_condition):
    emojis = {
        "Clear": "☀️", "Clouds": "☁️", "Rain": "🌧️", "Thunderstorm": "⛈️",
        "Snow": "❄️", "Drizzle": "🌦️", "Mist": "🌫️", "Smoke": "🌫️",
        "Haze": "🌫️", "Dust": "🌪️", "Fog": "🌫️"
    }
    return emojis.get(weather_condition, "😶‍🌫️")


def generate_health_alerts(weather_data):
    alerts = []
    
    # High temperature alert
    temp = weather_data['main']['temp']
    if temp > 30:  # High temperature threshold
        alerts.append("High temperature detected. Stay hydrated and avoid prolonged exposure to the sun.")

    # Low temperature alert
    if temp < 0:  # Low temperature threshold
        alerts.append("Low temperature detected. Dress warmly to prevent hypothermia.")

    # High humidity alert
    humidity = weather_data['main']['humidity']
    if humidity > 80:
        alerts.append("High humidity detected. Stay hydrated and monitor respiratory conditions.")
    
    return alerts


def generate_weather_recommendations(weather_data):
    temp = weather_data['main']['temp']
    weather_condition = weather_data['weather'][0]['main']

    recommendations = []

    # Suggest based on temperature and weather condition
    if weather_condition in ['Rain']:
        recommendations.append("It's rainy outside. How about indoor activities like visiting a museum or watching a film?")
    elif weather_condition == 'Thunderstorm':
        recommendations.append("Thunderstorms! Best to stay indoors and enjoy a warm meal or a good book.")
    elif weather_condition == 'Snow':
        recommendations.append("It's snowing! Perfect time for some winter sports or building a snowman.")
    elif temp > 30:  # Hot weather
        recommendations.append("It's hot outside! How about going for a swim or relaxing indoors with some cold drinks?")
    elif temp > 20:  # Warm weather
        recommendations.append("Perfect weather for a hike or a picnic in the park!")
    elif temp > 10:  # Cool weather
        recommendations.append("It's a bit chilly. Maybe enjoy a cozy walk or a coffee at a café.")
    elif temp > 0:  # Cold weather
        recommendations.append("It's quite cold outside. Bundle up and consider indoor activities like reading or watching a movie.")
    else:  # Freezing temperatures
        recommendations.append("Freezing temperatures! Stay indoors, perhaps enjoy a hot drink or a movie marathon.")


    return recommendations


@dispatch(str, str)
def get_weather_data(location, units):
    weather_response = requests.get(f"{BASE_URL}?q={location}&appid={API_KEY}&units={units}")
    return weather_response.json()

@dispatch(str)
def get_weather_data(location):
    return get_weather_data(location, 'metric')


@dispatch(str, str)
def get_forecast_data(location, units):
    forecast_response = requests.get(f"{FORECAST_URL}?q={location}&appid={API_KEY}&units={units}")
    return forecast_response.json()

@dispatch(str)
def get_forecast_data(location):
    return get_forecast_data(location, 'metric')


@app.route('/weather', methods=['POST'])
def weather():
    location = request.form.get('location')
    units = request.form.get('units', 'metric')  # Optional unit parameter from the form

    weather_data = get_weather_data(location, units)
    forecast_data = get_forecast_data(location, units)

    if 'main' in weather_data and 'list' in forecast_data:
        try:
            current_temp = weather_data['main']['temp']
            weather_emoji = get_weather_emoji(weather_data['weather'][0]['main'])
            humidity = weather_data['main']['humidity']
            pressure = weather_data['main']['pressure']
            visibility = weather_data['visibility'] / 1000  # Convert to km
            feels_like = weather_data['main']['feels_like']
            sunrise = datetime.datetime.fromtimestamp(weather_data['sys']['sunrise']).strftime('%I:%M %p')
            sunset = datetime.datetime.fromtimestamp(weather_data['sys']['sunset']).strftime('%I:%M %p')

            # Generate health alerts based on current weather data
            health_alerts = generate_health_alerts(weather_data)
            
            # Generate weather recommendations
            weather_recommendations = generate_weather_recommendations(weather_data)

            forecast_list = process_forecast_data(forecast_data)

            return render_template(
                'index.html',
                location=location,
                current_temp=current_temp,
                weather_emoji=weather_emoji,
                forecast_list=forecast_list,
                humidity=humidity,
                pressure=pressure,
                visibility=visibility,
                feels_like=feels_like,
                sunrise=sunrise,
                sunset=sunset,
                health_alerts=health_alerts,
                weather_recommendations=weather_recommendations  # Pass recommendations to template
            )
        except (KeyError, TypeError) as e:
            return render_template('index.html', error="Error retrieving weather data.")
    else:
        return render_template('index.html', error="Location not found.")


def process_forecast_data(forecast_data):
    daily_temps = {}
    for forecast in forecast_data.get('list', []):  # Use .get() to avoid KeyError
        date_time = datetime.datetime.fromtimestamp(forecast['dt'])
        date = date_time.date()

        if date not in daily_temps or forecast['main']['temp'] > daily_temps[date]['temp']:
            daily_temps[date] = {
                'temp': forecast['main']['temp'],
                'weather_emoji': get_weather_emoji(forecast['weather'][0]['main']),
            }

    forecast_list = [
        {'date': date.strftime('%d/%m/%Y'), 'temp': temp_info['temp'], 'weather_emoji': temp_info['weather_emoji']}
        for date, temp_info in daily_temps.items()
    ]

    return forecast_list


if __name__ == '__main__':
    app.run(debug=True)

