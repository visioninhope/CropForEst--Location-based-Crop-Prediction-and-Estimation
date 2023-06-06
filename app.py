import joblib
import requests, os
import pandas as pd
from flask import Flask, jsonify, request, render_template
from sklearn.calibration import LabelEncoder
from sklearn.discriminant_analysis import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Get form data
        district = request.form['district']
        n = float(request.form['n'])
        p = float(request.form['p'])
        k = float(request.form['k'])

        total = n + p + k
        n = n / total
        p = p / total
        k = k / total
        print (n,p,k)
        # Get weather data from OpenWeatherMap API
        weather_api_key = '4b69e9c09afabe33e9c0aa775a8400ce'
        url = f'http://api.openweathermap.org/data/2.5/weather?q={district}&appid={weather_api_key}'
        response = requests.get(url).json()
        print(response)
        temp = response['main']['temp'] - 2734
        humidity = response['main']['humidity']
        rainfall = float(request.form['rainfall'])
        print(temp, humidity)

        # Load crop prediction model and predict crop
        crop_prediction_model = joblib.load('prediction.pkl')
        crop_prediction_input = [[temp, humidity, rainfall, n, p, k]]
        predicted_crop = crop_prediction_model.predict(crop_prediction_input)[0]
        print ( "\n Predicted Crop = " , predicted_crop)

        # Load price estimation model and predict crop price
        price_estimation_model = joblib.load('estimation.pkl')
        df = pd.read_csv('Price_Sorted_Modified.csv')
        le_district = LabelEncoder()
        df['District'] = le_district.fit_transform(df['District'])
        le_crop = LabelEncoder()
        df['Crop'] = le_crop.fit_transform(df['Crop'])
        df['Price Date'] = pd.to_datetime(df['Price Date'], format='%b-%Y')
        df['Month'] = df['Price Date'].dt.month
        df['Year'] = df['Price Date'].dt.year
        df = df.drop('Price Date', axis=1)

        # Split the dataset into training and testing sets
        X_train, X_test, y_train, y_test = train_test_split(df[['District', 'Crop', 'Month', 'Year']], df['Crop Price (Rs per quintal)'], test_size=0.2, random_state=42)
        imputer = SimpleImputer()
        X_train = imputer.fit_transform(X_train)
        X_test = imputer.transform(X_test)

        # Feature scaling
        scaler = StandardScaler()
        X_train = scaler.fit_transform(X_train)
        X_test = scaler.transform(X_test)

        today = pd.Timestamp.today()
        next_six_months = pd.date_range(today, periods=12, freq='MS').strftime("%m-%Y").tolist()
        next_six_months_df = pd.DataFrame({'District': [le_district.transform([district])[0]]*12,
                                        'Crop': [le_crop.transform([predicted_crop])[0]]*12,
                                        'Month': [int(month.split('-')[0]) for month in next_six_months],
                                        'Year': [int(month.split('-')[1]) for month in next_six_months]})

        # Use the trained XGBoost model to make predictions on the next 12 months dataset
        next_six_months_df = imputer.transform(next_six_months_df)
        next_six_months_df = scaler.transform(next_six_months_df)
        print ("\n ALL GOOD !")
        predicted_price = price_estimation_model.predict(next_six_months_df)
        next12months = pd.date_range(today, periods=12, freq='MS')
        months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
        print(predicted_price)
        price_data = [{'month': month.strftime('%B %Y'), 'price': price} for month, price in zip(next12months, predicted_price.tolist())]
        print(price_data)

        # Send result to front end
        result = {'crop': predicted_crop, 'price_data': price_data}
        crop_info = [{'crop': 'Rice', 'info': 'Rice is mainly cultivated in the Cauvery delta region, and other important rice-growing areas include the districts of Nagapattinam, Thanjavur, Tiruvarur, and Pudukkottai. Rice is grown in Tamil Nadu from June to September. It requires warm and humid weather conditions and well-drained fertile soil for optimal growth. The crop is highly dependent on rainfall and proper irrigation facilities. Tamil Nadu produces a variety of rice cultivars such as Samba, Ponni, and Mappillai Samba, among others.'},
             {'crop': 'Maize', 'info': 'Maize is a kharif crop that is widely cultivated in Tamil Nadu. It is an important source of food, feed, and fuel. The crop requires a warm and moist climate for growth and is generally sown in June and harvested in October. The ideal temperature range for maize cultivation is between 20°C and 30°C. The crop is grown in areas with good rainfall and well-drained soils. In Tamil Nadu, maize is mainly grown in the districts of Coimbatore, Salem, Erode, and Dindigul. Maize is an important crop for farmers as it provides good returns and is also used as a feed for poultry and livestock.'},
             {'crop': 'Cotton', 'info': 'Cotton is one of the important cash crops grown in Tamil Nadu, especially in the southern parts of the state. It requires well-drained soil, a warm climate with high temperatures ranging from 21°C to 30°C, and an average rainfall of 600 to 700 mm. The sowing season for cotton is from February to March, and harvesting is done from June to September. In Tamil Nadu, the major cotton-growing districts are Coimbatore, Dindigul, Madurai, Theni, Tiruppur, and Trichy. The main pests affecting cotton in Tamil Nadu are aphids, jassids, and whiteflies, which can be controlled by using neem-based pesticides.'},
             {'crop': 'Coconut', 'info': 'Coconut is an important crop in Tamil Nadu, with the state being one of the major producers of coconuts in India. The crop is grown throughout the year, but the main season for coconut cultivation in the state is from May to October.Coconut trees require a warm, humid climate with plenty of rainfall, and Tamil Nadus coastal areas provide ideal growing conditions for the crop. The ideal temperature range for coconut growth is between 20-32°C, and the crop requires well-drained soils with good water retention capacity.'},
             {'crop': 'Banana', 'info': 'Banana is a popular fruit crop grown in Tamil Nadu, a state located in the southern part of India. The state has favorable agro-climatic conditions for banana cultivation, including a long growing season, warm temperatures, and high humidity. The best time to plant banana in Tamil Nadu is during the months of June and July, with the crop being ready for harvesting in about 10-12 months. Bananas require well-drained soil with a pH range of 6-7 and a temperature range of 20-30°C.'},
             {'crop': 'Black Gram', 'info': 'Black gram, also known as urad bean, is an important crop in Tamil Nadu, India. It is typically grown during the Kharif season, which lasts from August to November. Black gram requires a warm and humid climate, with temperatures ranging from 25-35°C and a rainfall of 800-1000 mm during its growing period. The soil for cultivation should be well-drained, fertile and rich in organic matter. In Tamil Nadu, black gram is cultivated mainly in the districts of Villupuram, Kanchipuram, Tiruvallur, and Vellore. Black gram is a rich source of protein, and its cultivation plays an important role in the economy of Tamil Nadu.'},
             {'crop': 'Green Gram', 'info': 'Green gram is an important kharif pulse crop that is widely cultivated in Tamil Nadu, a southern state of India. The crop requires a warm and humid climate with temperatures ranging from 25-35°C and well-distributed rainfall between 500-600 mm. It can be grown in a variety of soils but performs best in well-drained loamy soils. In Tamil Nadu, the crop is sown during the months of August to September and harvested in December. The state is one of the major producers of green gram in the country, with the districts of Tiruchirappalli, Coimbatore, and Erode being major cultivation areas. Green gram is valued for its high protein content and is used in various culinary preparations.'},
             {'crop': 'Red Gram', 'info': 'Red gram, also known as pigeon pea, is an important pulse crop grown in Tamil Nadu. It is a drought-tolerant crop and can be cultivated in a variety of soils. The best time for sowing red gram in Tamil Nadu is between June and August. It requires warm and humid weather with a temperature range of 25 to 30 degrees Celsius for optimal growth. Red gram crop is susceptible to waterlogging and hence requires well-drained soil. It is an important crop for both subsistence and commercial farming in Tamil Nadu, with the crop being used for a variety of purposes such as food, fodder, and fuel.'},
             {'crop': 'Bengal Gram', 'info': 'Bengal Gram, also known as Chana or Chickpea, is a widely cultivated pulse crop in Tamil Nadu, India. The crop requires a warm and dry climate, with an ideal temperature range of 20-25°C during the growing season. It grows well in well-drained loamy soils with a pH range of 6.0-7.5. The crop is usually sown in the post-monsoon season, from October to December, and harvested in March to April. Bengal Gram is an important source of protein and essential nutrients, and it is used in a variety of culinary dishes such as curries, stews, and salads. Its high protein content makes it a valuable crop for both human consumption and animal feed.'},
             {'crop': 'Coffee', 'info': 'Coffee is an important commercial crop in Tamil Nadu, with the state accounting for about 17% of Indias coffee production. Arabica and Robusta are the two main varieties of coffee grown in Tamil Nadu, with Arabica being the more popular one. Coffee requires a warm and humid climate for its growth, with an average temperature range of 20-28°C and an annual rainfall of 1500-2500 mm. The crop grows best in well-drained, loamy soils with a pH range of 6.0-6.5. The major coffee-growing areas in Tamil Nadu include the Nilgiris, Coorg, and Shevaroys, which are known for their unique coffee flavor and aroma. Coffee is usually grown under shade trees, and intercropping with other crops like pepper and cardamom is also practiced to maximize land use efficiency.'}]
        # print(result)
        #print(type(result.price_data))
        return render_template('result.html', result=result, crop_info = crop_info)
    else:
        return render_template('index.html')

# print(results)
# @app.route('/result', methods = ['GET', 'POST'])
# def result():
#     if request.method == 'POST':
#         return render_template('result.html', result=results)
#     else:
#         return render_template('index.jt,l')