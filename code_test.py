import requests
import json
import time
import pandas as pd
import schedule
import smtplib
from datetime import datetime
import matplotlib.pyplot as plt

# API key and cities
API_KEY = 'd1b5ea14d140e1379a64fb642599a700'  # Replace with your OpenWeatherMap API key
CITIES = ['Delhi', 'Mumbai', 'Chennai', 'Bangalore', 'Kolkata', 'Hyderabad']
URL = "http://api.openweathermap.org/data/2.5/weather?q={}&appid={}"

MINUTES = 1

# To store daily weather data for each city
weather_data = {city: [] for city in CITIES}


def fetch_weather_data():
    for city in CITIES:
        response = requests.get(URL.format(city, API_KEY))
        if response.status_code == 200:
            data = response.json()
            process_weather_data(city, data)
        else:
            print(f"Failed to get data for {city}. Status code: {response.status_code}")

    # Debug: Print fetched data after each fetch
    print("Weather Data Fetched:")
    for city in CITIES:
        print(f"{city}: {weather_data[city]}")

# Function to process and store data
def process_weather_data(city, data):
    # Convert temperature from Kelvin to Celsius
    temp_celsius = data['main']['temp'] - 273.15
    feels_like_celsius = data['main']['feels_like'] - 273.15
    humidity = data['main']['humidity']
    wind_speed = data['wind']['speed']
    weather_condition = data['weather'][0]['main']
    timestamp = data['dt']
    
    # Print data to check structure
    print(f"Storing data for {city}: {timestamp}, {temp_celsius:.2f}°C, Humidity: {humidity}%")
    
    # Store the data
    weather_data[city].append({
        'city': city,
        'temp': temp_celsius,
        'feels_like': feels_like_celsius,
        'humidity': humidity,
        'wind_speed': wind_speed,
        'weather': weather_condition,
        'timestamp': timestamp
    })

# Schedule the API call every N minutes
schedule.every(MINUTES).minutes.do(fetch_weather_data)

# Calculate daily summary for each city
def calculate_daily_summary():
    today = datetime.now().strftime('%Y-%m-%d')
    for city, data in weather_data.items():
        # Convert to DataFrame for easier calculation
        df = pd.DataFrame(data)
        
        # Filter data for the current day
        df['date'] = pd.to_datetime(df['timestamp'], unit='s').dt.date
        df_today = df[df['date'] == pd.to_datetime(today).date()]
        
        if not df_today.empty:
            avg_temp = df_today['temp'].mean()
            max_temp = df_today['temp'].max()
            min_temp = df_today['temp'].min()
            dominant_weather = df_today['weather'].mode()[0]  # Most frequent weather condition
            
            # Explanation for dominant weather condition (e.g., why "Rain" is chosen)
            dominant_weather_reason = f"The weather condition '{dominant_weather}' appeared the most frequently today."
            
            print(f"Daily Summary for {city} on {today}:")
            print(f"Avg Temp: {avg_temp:.2f}°C, Max Temp: {max_temp:.2f}°C, Min Temp: {min_temp:.2f}°C")
            print(f"Dominant Weather Condition: {dominant_weather}")
            print(f"Explanation: {dominant_weather_reason}")
            
            # Save to persistent storage (CSV for simplicity here)
            df_today.to_csv(f"{city}_{today}_weather_summary.csv", index=False)
        else:
            print(f"No data available for {city} on {today}")

# Schedule daily summary at midnight
schedule.every().day.at("00:00").do(calculate_daily_summary)

# User-defined thresholds
TEMP_THRESHOLD = 35  # degrees Celsius
HUMIDITY_THRESHOLD = 80  # percentage
ALERT_CONSECUTIVE_LIMIT = 2  # number of consecutive updates
WEATHER_CONDITION_ALERTS = ["Rain", "Storm"]  # Configurable alert for specific conditions

# Function to check for alerts
def check_alerts():
    for city, data in weather_data.items():
        # Check last few updates
        if len(data) >= ALERT_CONSECUTIVE_LIMIT:
            recent_data = data[-ALERT_CONSECUTIVE_LIMIT:]
            
            # Temperature alert
            if all(d['temp'] > TEMP_THRESHOLD for d in recent_data):
                alert_msg = f"ALERT: {city} temperature has exceeded {TEMP_THRESHOLD}°C for the last {ALERT_CONSECUTIVE_LIMIT} updates!"
                print(alert_msg)
                send_email_alert(city, alert_msg)
            
            # Humidity alert
            if all(d['humidity'] > HUMIDITY_THRESHOLD for d in recent_data):
                alert_msg = f"ALERT: {city} humidity has exceeded {HUMIDITY_THRESHOLD}% for the last {ALERT_CONSECUTIVE_LIMIT} updates!"
                print(alert_msg)
                send_email_alert(city, alert_msg)

            # Weather condition alert
            if any(d['weather'] in WEATHER_CONDITION_ALERTS for d in recent_data):
                alert_msg = f"ALERT: {city} has experienced {recent_data[-1]['weather']} in recent updates!"
                print(alert_msg)
                send_email_alert(city, alert_msg)

# Function to send email alerts (optional)
def send_email_alert(city, message):
    print("Sending email alert...")
    print(f"City: {city}\nMessage: {message}")
    # Email sending code would be here

# Schedule alert checking after every update
schedule.every(MINUTES).minutes.do(check_alerts)

# Function to plot temperature trends for a city (last N days)
def plot_weather_trends(city, days=1):
    # Check if data for the city exists
    if city not in weather_data or not weather_data[city]:
        print(f"No weather data available for {city}.")
        return
    
    # Convert weather_data into a DataFrame
    df = pd.DataFrame(weather_data[city])
    
    # Debug: Print DataFrame to inspect
    print("DataFrame contents:")
    print(df.head())
    
    # Convert timestamp to datetime format
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
    
    # Filter for the last N days
    cutoff_time = datetime.now() - pd.Timedelta(days=days)
    recent_data = df[df['datetime'] >= cutoff_time]
    
    # Debug: Print filtered data
    print(f"Filtered data for last {days} days:")
    print(recent_data)
    
    if recent_data.empty:
        print(f"No data available for {city} in the last {days} days.")
        return
    
    # Plot temperature trends
    plt.figure(figsize=(10, 6))
    plt.plot(recent_data['datetime'], recent_data['temp'], label="Temperature (°C)", color='b')
    plt.xlabel('Time')
    plt.ylabel('Temperature (°C)')
    plt.title(f"Weather Trends for {city} (Last {days} Days)")
    plt.legend()
    plt.grid(True)
    plt.show()
    
# Test Cases
def run_test_cases():
    # Test case 1: Data retrieval
    print("Test Case 1: Fetching data...")
    fetch_weather_data()
    
    # Test case 2: Temperature conversion
    print("Test Case 2: Testing temperature conversion (Kelvin to Celsius)...")
    assert all(d['temp'] < 100 for city in CITIES for d in weather_data[city]), "Temperature conversion failed!"
    
    # Test case 3: Daily summary calculation
    print("Test Case 3: Daily weather summary calculation...")
    calculate_daily_summary()
    
    # Test case 4: Alerts system
    print("Test Case 4: Checking alert system...")
    check_alerts()

if __name__ == "__main__":
    print("Starting Weather Monitoring System...")
    
    # Initial data fetch
    fetch_weather_data()
    
    # Wait until weather data for Delhi is available
    while not weather_data['Delhi']:
        print("Waiting for weather data...")
        time.sleep(1)
    
    # Now that data is available, plot trends for Delhi
    plot_weather_trends('Delhi', days=1)
    
    # Run test cases
    run_test_cases()
    
    # Keep the scheduler running
    while True:
        schedule.run_pending()
        time.sleep(1)
