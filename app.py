# -*- coding: utf-8 -*-
"""
Created on Fri Aug 16 08:33:29 2024

@author: Hp
"""

import streamlit as st
import requests
from datetime import datetime, timedelta

# API keys
api_key = "KnG3nqSMshXGm1nXdb1Ab4uGWABuQuTO"
api_secret = "ULJAYtod0e3cZhCG"

# Function to get the access token
def get_access_token(api_key, api_secret):
    url = "https://test.api.amadeus.com/v1/security/oauth2/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",
        "client_id": api_key,
        "client_secret": api_secret
    }
    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        st.error("Failed to get access token")
        return None

# Function to get the lowest fares
def get_monthly_lowest_fares(access_token, origin, destination, year, month, airlines, num_airlines=3):
    days_in_month = (datetime(year, month + 1, 1) - timedelta(days=1)).day
    all_flights = []

    for day in range(1, days_in_month + 1):
        date = f"{year}-{month:02d}-{day:02d}"
        url = f"https://test.api.amadeus.com/v2/shopping/flight-offers"
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {
            "originLocationCode": origin,
            "destinationLocationCode": destination,
            "departureDate": date,
            "adults": "1",
            "currencyCode": "INR",
            "max": "10"
        }

        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            flights = response.json().get('data', [])
            flights = [flight for flight in flights if flight['validatingAirlineCodes'][0] in airlines]
            all_flights.extend(flights)
        else:
            st.warning(f"Failed to retrieve data for {date}: {response.status_code}")
            continue

    all_flights = sorted(all_flights, key=lambda x: x['price']['total'])
    lowest_fares = []

    for flight in all_flights[:num_airlines]:
        itinerary = flight['itineraries'][0]
        segment = itinerary['segments'][0]
        date = segment['departure']['at'][:10]
        airline = flight['validatingAirlineCodes'][0]
        price = flight['price']['total']
        flight_number = segment['carrierCode'] + segment['number']
        departure_time = segment['departure']['at']
        arrival_time = segment['arrival']['at']
        
        lowest_fares.append({
            "date": date,
            "airline": airline,
            "price": price,
            "flight_number": flight_number,
            "departure_time": departure_time,
            "arrival_time": arrival_time
        })

    return lowest_fares

# Streamlit App Interface
st.title("Monthly Lowest Airfares Finder")

# Input fields
origin = st.text_input("Origin Airport Code", "DEL")
destination = st.text_input("Destination Airport Code", "BOM")
year = st.number_input("Year", min_value=2023, max_value=2030, value=2024)
month = st.number_input("Month", min_value=1, max_value=12, value=9)
selected_airlines = st.multiselect("Select Airlines", ["6E", "AI", "UK"], default=["6E", "AI", "UK"])

if st.button("Find Lowest Fares"):
    # Get access token
    access_token = get_access_token(api_key, api_secret)
    if access_token:
        # Get the lowest fares
        lowest_fares = get_monthly_lowest_fares(access_token, origin, destination, year, month, selected_airlines)
        if lowest_fares:
            st.success(f"Lowest fares for {month}/{year}:")
            for fare in lowest_fares:
                st.write(f"**{fare['date']}**: {fare['airline']} - ₹{fare['price']}")
                st.write(f"Flight Number: {fare['flight_number']}")
                st.write(f"Departure Time: {fare['departure_time']}")
                st.write(f"Arrival Time: {fare['arrival_time']}")
                st.write("-" * 40)
        else:
            st.warning("No flights found.")
