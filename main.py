from flask import Flask, request, send_file
import pandas as pd
from prophet import Prophet

# create the Flask app
app = Flask(__name__)

@app.route('/covid')
def predict():
    zipcode = request.args.get('zipcode')
    horizon = request.args.get('horizon', type=int)
    
    df = pd.read_csv('COVID19_Cases.csv')
    df_zipcode = df[df['ZIP Code']==zipcode].rename(columns = {'Week Start': 'ds','Cases - Weekly': 'y'})
 
    model = Prophet(interval_width=0.95)
    model.fit(df_zipcode) 
    future_dates = model.make_future_dataframe(periods = horizon, freq="W", include_history=False)
    forecast = model.predict(future_dates)
    fig=model.plot(forecast, xlabel="Weeks", ylabel="Weekly Covid Cases for Zipcode: " + zipcode)
    fig.savefig('prophetplot.svg')
    return send_file('prophetplot.svg')

if __name__ == '__main__':
    # run app in debug mode on port 5000
    app.run(debug=True, host="0.0.0.0", port=5000)