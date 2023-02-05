import firebase_admin
from firebase_admin import credentials


cred = credentials.Certificate("configs/configs.json")
app = firebase_admin.initialize_app(cred)

firebase_config = {
  "apiKey": "AIzaSyBUIR5klycxrSWUrH3etnieNWI0hCHoCaE",
  "authDomain": "todayfleet.firebaseapp.com",
  "databaseURL": "https://todayfleet-default-rtdb.firebaseio.com",
  "projectId": "todayfleet",
  "storageBucket": "todayfleet.appspot.com",
  "messagingSenderId": "291334526686",
  "appId": "1:291334526686:web:049cb35a38a8c5aae4944f",
  "measurementId": "G-SWN1PX74ZK"
}