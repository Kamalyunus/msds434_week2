from flask import Flask, request, send_file
import pandas as pd
from prophet import Prophet
from google.cloud.sql.connector import Connector
import sqlalchemy
import pg8000

# create the Flask app
app = Flask(__name__)

# initialize Cloud SQL Python Connector object
connector = Connector()
def getconn()->pg8000.dbapi.Connection:
    conn: pg8000.dbapi.Connection = connector.connect(
        "cbi-yunus:us-central1:cbipostgres",
        "pg8000",
        user="postgres",
        password="root",
        db="chicago_business_intelligence"
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
    with pool.connect() as db_conn:
        query="SELECT * FROM covid_weekly WHERE zip_code='"+zipcode+"'"
        df = pd.read_sql_query(query, db_conn)

    df_zipcode = df.rename(columns = {'week_start': 'ds','cases_weekly': 'y'})
    df_zipcode['ds'] = df_zipcode['ds'].dt.date
    model = Prophet(interval_width=0.95)
    model.fit(df_zipcode) 
    future_dates = model.make_future_dataframe(periods = horizon, freq="W", include_history=False)
    forecast = model.predict(future_dates)
    fig=model.plot(forecast, xlabel="Weeks", ylabel="Weekly Covid Cases for Zipcode: " + zipcode)
    fig.savefig('prophetplot.svg')
    connector.close()
    return send_file('prophetplot.svg')

if __name__ == '__main__':
    # run app in debug mode on port 5000
    app.run(debug=True, host="0.0.0.0", port=5000)