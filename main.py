from flask import Flask, request, send_file
import pandas as pd
from prophet import Prophet
import os
from google.cloud.sql.connector import Connector
import sqlalchemy

# create the Flask app
app = Flask(__name__)

INSTANCE_CONNECTION_NAME="cbi-yunus:us-central1:cbipostgres"
DB_USER = os.environ["DB_USER"]
DB_PASS = os.environ["DB_PASS"]
DB_NAME = os.environ["DB_NAME"]

# initialize Cloud SQL Python Connector object
connector = Connector()
def getconn():
    conn = connector.connect(
        INSTANCE_CONNECTION_NAME,
        "pg8000",
        user=DB_USER,
        password=DB_PASS,
        db=DB_NAME
    )
    return conn

pool = sqlalchemy.create_engine(
    "postgresql+pg8000://",
    creator=getconn,
    pool_size=5,
    max_overflow=2,
    pool_timeout=30,  
    pool_recycle=1800,
    # [END_EXCLUDE]
)
    

@app.route('/covid')
def predict():
    zipcode = request.args.get('zipcode')
    horizon = request.args.get('horizon', type=int)
    with pool.connect as db_conn:
        results = db_conn.execute("SELECT * FROM covid_weekly limit 5").fetchall()

    df = pd.read_csv('COVID19_Cases.csv')
    df_zipcode = df[df['ZIP Code']==zipcode].rename(columns = {'Week Start': 'ds','Cases - Weekly': 'y'})
 
    model = Prophet(interval_width=0.95)
    model.fit(df_zipcode) 
    future_dates = model.make_future_dataframe(periods = horizon, freq="W", include_history=False)
    forecast = model.predict(future_dates)
    fig=model.plot(forecast, xlabel="Weeks", ylabel="Weekly Covid Cases for Zipcode: " + zipcode)
    fig.savefig('prophetplot.svg')
    #return send_file('prophetplot.svg')
    return results

if __name__ == '__main__':
    # run app in debug mode on port 5000
    app.run(debug=True, host="0.0.0.0", port=5000)