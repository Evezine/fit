import streamlit as st
from pymongo import MongoClient
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import datetime
from datetime import datetime as dt

# MongoDB connection to local server
client = MongoClient("mongodb://localhost:27017/")
db = client['fitness_tracker']

# Collections
users_collection = db['users']
workouts_collection = db['workouts']

# User Authentication
def signup(username, password):
    if users_collection.find_one({'username': username}):
        st.error("Username already exists.")
    else:
        users_collection.insert_one({'username': username, 'password': password})
        st.success("Signup successful! Please log in.")

def login(username, password):
    user = users_collection.find_one({'username': username})
    if user and user['password'] == password:
        st.session_state['logged_in'] = True
        st.session_state['username'] = username
        st.success("Logged in successfully!")
    else:
        st.error("Invalid username or password.")

# Add workout data
def add_workout(username, date, workout_type, duration, calories):
    # Convert date to datetime.datetime
    datetime_date = dt.combine(date, dt.min.time())
    
    workouts_collection.insert_one({
        'username': username,
        'date': datetime_date,  # Store as datetime.datetime
        'workout_type': workout_type,
        'duration': duration,
        'calories': calories
    })
    st.success("Workout data added successfully!")

# Get user workout data
def get_user_data(username):
    return pd.DataFrame(list(workouts_collection.find({'username': username})))

# Export to CSV
def export_data_to_csv(data, username):
    csv_data = data.to_csv(index=False).encode('utf-8')
    st.download_button(label=f"Download {username}'s Data as CSV", data=csv_data, file_name=f"{username}_fitness_data.csv", mime='text/csv')

# Display leaderboard
def display_leaderboard():
    pipeline = [
        {"$group": {"_id": "$username", "total_calories": {"$sum": "$calories"}}},
        {"$sort": {"total_calories": -1}}
    ]
    leaderboard_data = list(workouts_collection.aggregate(pipeline))
    leaderboard_df = pd.DataFrame(leaderboard_data)
    leaderboard_df.columns = ['Username', 'Total Calories Burned']
    st.subheader("Leaderboard")
    st.dataframe(leaderboard_df)

# Streamlit UI
st.title("Fitness Tracker")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if st.session_state['logged_in']:
    st.sidebar.write(f"Welcome, {st.session_state['username']}")
    action = st.sidebar.selectbox("Choose an action", ["Add Workout", "View Progress", "Leaderboard", "Logout"])

    if action == "Add Workout":
        st.subheader("Add Workout")
        workout_type = st.selectbox("Workout Type", ["Running", "Cycling", "Swimming", "Yoga", "Gym"])
        duration = st.number_input("Duration (minutes)", min_value=1)
        calories = st.number_input("Calories Burned", min_value=1)
        date = st.date_input("Date", value=datetime.date.today())
        if st.button("Add Workout"):
            add_workout(st.session_state['username'], date, workout_type, duration, calories)

    elif action == "View Progress":
        st.subheader("Your Workout Progress")
        user_data = get_user_data(st.session_state['username'])
        if not user_data.empty:
            user_data['date'] = pd.to_datetime(user_data['date'])

            # Line chart with Plotly
            fig = px.line(user_data, x='date', y='calories', title='Calories Burned Over Time', markers=True)
            st.plotly_chart(fig)

            # Bar chart with Matplotlib
            plt.figure(figsize=(10, 5))
            user_data.groupby('workout_type')['calories'].sum().plot(kind='bar', color='skyblue')
            plt.title('Total Calories Burned by Workout Type')
            plt.xlabel('Workout Type')
            plt.ylabel('Calories Burned')
            st.pyplot(plt)

            export_data_to_csv(user_data, st.session_state['username'])
        else:
            st.write("No workout data available.")

    elif action == "Leaderboard":
        display_leaderboard()

    elif action == "Logout":
        st.session_state['logged_in'] = False
        st.session_state['username'] = None
        st.success("Logged out successfully.")

else:
    auth_choice = st.selectbox("Sign In or Sign Up", ["Sign In", "Sign Up"])
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if auth_choice == "Sign Up":
        if st.button("Sign Up"):
            signup(username, password)
    elif auth_choice == "Sign In":
        if st.button("Sign In"):
            login(username, password)
