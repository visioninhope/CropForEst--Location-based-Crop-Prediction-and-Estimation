// get references to the form elements
const form = document.getElementById('prediction-form');
const districtInput = document.getElementById('district');
const nInput = document.getElementById('n');
const pInput = document.getElementById('p');
const kInput = document.getElementById('k');
const rainfallInput = document.getElementById('rainfall');
const submitButton = document.getElementById('submit-button');

// add event listener to the form for form submission
form.addEventListener('submit', (event) => {
  // prevent default form submission behavior
  event.preventDefault();

  // get the values from the form
  const district = districtInput.value;
  const n = parseFloat(nInput.value);
  const p = parseFloat(pInput.value);
  const k = parseFloat(kInput.value);
  const rainfall = parseFloat(rainfallInput.value);

  // get weather data from OpenWeatherMap API
  const apiKey = '4b69e9c09afabe33e9c0aa775a8400ce';
  const url = `https://api.openweathermap.org/data/2.5/weather?q=${district}&appid=${apiKey}&units=metric`;
  fetch(url)
    .then(response => response.json())
    .then(data => {
      const temperature = data.main.temp;
      const humidity = data.main.humidity;

      // call the prediction API to get the predicted crop
      const predictionUrl = 'http://localhost:5000/predict';
      const predictionData = {
        district,
        rainfall,
        n,
        p,
        k,
        temperature,
        humidity,
      };
      fetch(predictionUrl, {
        method: 'POST',
        body: JSON.stringify(predictionData),
        headers: {
          'Content-Type': 'application/json',
        },
      })
        .then(response => response.json())
        .then(data => {
          const crop = data.crop;

          // call the estimation API to get the predicted prices
          const estimationUrl = 'http://localhost:5000/estimate';
          const estimationData = {
            crop,
            district,
          };
          fetch(estimationUrl, {
            method: 'POST',
            body: JSON.stringify(estimationData),
            headers: {
              'Content-Type': 'application/json',
            },
          })
            .then(response => response.json())
            .then(data => {
              const priceData = data.price_data;
              // update the table with the predicted prices
              const priceTable = document.getElementById('price-table');
              priceTable.innerHTML = `
                <thead>
                  <tr>
                    <th>Month</th>
                    <th>Price (Rs/kg)</th>
                  </tr>
                </thead>
                <tbody>
                  ${priceData.map(price => `
                    <tr>
                      <td>${price.month}</td>
                      <td>${price.price.toFixed(2)}</td>
                    </tr>
                  `).join('')}
                </tbody>
              `;
            })
            .catch(error => console.error('Error:', error));
        })
        .catch(error => console.error('Error:', error));
    })
    .catch(error => console.error('Error:', error));
});
