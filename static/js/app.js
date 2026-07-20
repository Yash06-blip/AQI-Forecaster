
// ── CONFIG ──
const API = "";

// ── AQI HELPERS ──
function getCategory(aqi) {
  if (aqi <= 50)  return { name:'Good',        color:'#55A84F', bg:'#E8F5E9', text:'#2E7D32' };
  if (aqi <= 100) return { name:'Satisfactory', color:'#A3C853', bg:'#F9FBE7', text:'#558B2F' };
  if (aqi <= 200) return { name:'Moderate',     color:'#E8C830', bg:'#FFF8E1', text:'#F57F17' };
  if (aqi <= 300) return { name:'Poor',         color:'#E93F33', bg:'#FBE9E7', text:'#BF360C' };
  if (aqi <= 400) return { name:'Very Poor',    color:'#AF2D24', bg:'#FCE4EC', text:'#880E4F' };
  return           { name:'Severe',             color:'#7E0023', bg:'#EDE7F6', text:'#4A148C' };
}

function getHealthAdvice(cat) {
  const advice = {
    'Good':        { icon:'🌿', text:'Great day to be outside! Air quality is healthy for everyone.' },
    'Satisfactory':{ icon:'✅', text:'Air quality is acceptable. Most people can go about their day normally.' },
    'Moderate':    { icon:'😷', text:'Children and elderly should reduce prolonged outdoor activity. Others can go out normally.' },
    'Poor':        { icon:'⚠️', text:'Everyone may begin to experience health effects. Avoid strenuous outdoor activity. Wear a mask if going out.' },
    'Very Poor':   { icon:'🚫', text:'Health warnings for everyone. Stay indoors as much as possible. Keep windows closed.' },
    'Severe':      { icon:'🔴', text:'Emergency conditions. Everyone should avoid all outdoor activity. Wear N95 masks if going out is necessary.' },
  };
  return advice[cat] || advice['Moderate'];
}

// ── GAUGE ──
function drawGauge(canvas, value, color) {
  const ctx = canvas.getContext('2d');
  const W = canvas.width, H = canvas.height;
  ctx.clearRect(0, 0, W, H);

  const cx = W / 2, cy = H - 10;
  const R = 120;
  const startAngle = Math.PI;
  const endAngle = 2 * Math.PI;

  // Background arc
  ctx.beginPath();
  ctx.arc(cx, cy, R, startAngle, endAngle);
  ctx.lineWidth = 20;
  ctx.strokeStyle = '#F0F0F0';
  ctx.lineCap = 'round';
  ctx.stroke();

  // Color segments
  const segments = [
    { max:50,  color:'#55A84F' },
    { max:100, color:'#A3C853' },
    { max:200, color:'#E8C830' },
    { max:300, color:'#E93F33' },
    { max:400, color:'#AF2D24' },
    { max:500, color:'#7E0023' },
  ];

  let prev = 0;
  segments.forEach(seg => {
    const segStart = startAngle + (prev/500) * Math.PI;
    const segEnd   = startAngle + (Math.min(value, seg.max)/500) * Math.PI;
    if (segEnd > segStart) {
      ctx.beginPath();
      ctx.arc(cx, cy, R, segStart, segEnd);
      ctx.lineWidth = 20;
      ctx.strokeStyle = seg.color;
      ctx.lineCap = 'butt';
      ctx.stroke();
    }
    prev = seg.max;
  });

  // Needle
  const angle = startAngle + (Math.min(value,500)/500) * Math.PI;
  const needleLen = R - 10;
  ctx.beginPath();
  ctx.moveTo(cx, cy);
  ctx.lineTo(
    cx + needleLen * Math.cos(angle),
    cy + needleLen * Math.sin(angle)
  );
  ctx.strokeStyle = '#1A1A2E';
  ctx.lineWidth = 3;
  ctx.lineCap = 'round';
  ctx.stroke();

  // Center dot
  ctx.beginPath();
  ctx.arc(cx, cy, 8, 0, 2*Math.PI);
  ctx.fillStyle = '#1A1A2E';
  ctx.fill();
}

// ── ANIMATED GAUGE ──
function animateGauge(canvas, target, color) {
  let current = 0;
  const step = target / 60;
  const tick = () => {
    current = Math.min(current + step, target);
    drawGauge(canvas, current, color);
    document.getElementById('gaugeValue').textContent = Math.round(current);
    if (current < target) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}

// ── HISTORICAL DATA ──
async function getHistoricalData() {
    try {
        const response = await fetch(`${API}/history`);

        if (!response.ok) {
            throw new Error("Failed to fetch history");
        }

        const data = await response.json();

        return {
            labels: data.dates,
            values: data.aqi_values
        };

    } catch (error) {
        console.error("Could not load historical data:", error);

        // fallback so the chart still renders
        return {
            labels: [],
            values: []
        };
    }
}


// ── CHART ──
let aqiChartInst;

async function buildChart(predictedAQI) {
  const { labels, values } = await getHistoricalData();
  const ctx = document.getElementById('aqiChart').getContext('2d');

  const forecastLabel = 'Tomorrow';
  const allLabels = [...labels, forecastLabel];
  const histData  = [...values, null];
  const forecastData = new Array(values.length).fill(null);
  forecastData.push(predictedAQI);

  // Zone fills
  const zones = {
    id: 'zones',
    beforeDatasetsDraw(chart) {
      const { ctx, chartArea: { left, right, top, bottom }, scales: { y } } = chart;
      const bands = [
        { min:0,   max:50,  color:'rgba(85,168,79,0.06)'  },
        { min:50,  max:100, color:'rgba(163,200,83,0.06)' },
        { min:100, max:200, color:'rgba(232,200,48,0.06)' },
        { min:200, max:300, color:'rgba(233,63,51,0.06)'  },
        { min:300, max:400, color:'rgba(175,45,36,0.06)'  },
        { min:400, max:500, color:'rgba(126,0,35,0.06)'   },
      ];
      bands.forEach(b => {
        const yTop = y.getPixelForValue(b.max);
        const yBot = y.getPixelForValue(b.min);
        ctx.fillStyle = b.color;
        ctx.fillRect(left, Math.max(top,yTop), right-left, Math.min(bottom,yBot)-Math.max(top,yTop));
      });
    }
  };

  if (aqiChartInst) aqiChartInst.destroy();

  aqiChartInst = new Chart(ctx, {
    type: 'line',
    data: {
      labels: allLabels,
      datasets: [
        {
          label: 'Historical AQI',
          data: histData,
          borderColor: '#4F7BE8',
          backgroundColor: 'rgba(79,123,232,0.08)',
          borderWidth: 2.5,
          pointRadius: 3,
          pointBackgroundColor: '#4F7BE8',
          tension: 0.4,
          fill: true,
          spanGaps: false,
        },
        {
          label: 'Forecast',
          data: forecastData,
          borderColor: '#E84F4F',
          borderDash: [6,4],
          borderWidth: 2.5,
          pointRadius: 8,
          pointBackgroundColor: '#E84F4F',
          pointBorderColor: '#fff',
          pointBorderWidth: 2,
          tension: 0,
          fill: false,
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#fff',
          borderColor: '#E8EAED',
          borderWidth: 1,
          titleColor: '#1A1A2E',
          bodyColor: '#6B7280',
          padding: 12,
          callbacks: {
            label: ctx => ` AQI ${Math.round(ctx.raw)} — ${getCategory(ctx.raw).name}`
          }
        }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: {
            font: { family:'DM Mono', size:11 },
            color: '#9CA3AF',
            maxTicksLimit: 10,
          }
        },
        y: {
          min: 0, max: 500,
          grid: { color: '#F3F4F6' },
          ticks: {
            font: { family:'DM Mono', size:11 },
            color: '#9CA3AF',
          }
        }
      }
    },
    plugins: [zones]
  });
}

// ── LOAD DEFAULT FORECAST ──
async function loadDefaultForecast() {
  const defaultPayload = {
    AQI_lag_24h: 235, AQI_lag_48h: 260, AQI_lag_72h: 245,
    AQI_lag_168h: 220, AQI_lag_8760h: 280,
    AQI_rolling_mean_24h: 248, AQI_rolling_mean_48h: 252,
    AQI_rolling_std_24h: 22.0, AQI_rolling_max_24h: 290,
    AQI_rolling_min_24h: 195,
    "PM2.5": 105.0, PM10: 162.0, NO2: 58.0,
    CO: 2.1, SO2: 16.0, O3: 24.0,
    temperature_lag_24h: 33.5, humidity_lag_24h: 58.0,
    windspeed_lag_24h: 11.0, precipitation_lag_24h: 0.0,
    temperature_rolling_mean_24h: 34.2, humidity_rolling_mean_24h: 55.0,
    windspeed_rolling_mean_24h: 10.5, precipitation_rolling_mean_24h: 0.0,
    forecast_datetime: new Date().toISOString().slice(0,19).replace('T',' ')
  };

  try {
    const res = await fetch(`${API}/forecast`, {
      method: 'POST',
      headers: { 'Content-Type':'application/json' },
      body: JSON.stringify(defaultPayload)
    });
    const data = await res.json();
    updateUI(data);
  } catch(e) {
    // API cold start — use fallback
    updateUI({
      predicted_AQI: 233,
      AQI_lower_bound: 194,
      AQI_upper_bound: 272,
      AQI_category: 'Poor',
      model_MAE: 39.3,
      model_MAPE_percent: 21,
      forecast_datetime: new Date().toISOString(),
      message: 'Predicted AQI for Delhi 24 hours from now is 233 (Poor)'
    });
  }
}

// ── UPDATE UI ──
async function updateUI(data) {
  const aqi  = Math.round(data.predicted_AQI);
  const cat  = getCategory(aqi);
  const adv  = getHealthAdvice(cat.name);
  const canvas = document.getElementById('gaugeCanvas');

  // Gauge
  animateGauge(canvas, aqi, cat.color);
  const catEl = document.getElementById('gaugeCategory');
  catEl.textContent = cat.name;
  catEl.style.background = cat.bg;
  catEl.style.color = cat.text;

  document.getElementById('gaugeSubtitle').textContent =
    `Predicted for tomorrow · based on today's conditions`;

  // Forecast card
  const headlines = {
    'Good':        'Tomorrow\'s air will be healthy.',
    'Satisfactory':'Tomorrow\'s air quality will be acceptable.',
    'Moderate':    'Moderate pollution expected tomorrow.',
    'Poor':        'Poor air quality expected tomorrow.',
    'Very Poor':   'Very poor air quality tomorrow. Take precautions.',
    'Severe':      'Severe pollution expected. Avoid going outside.',
  };
  document.getElementById('forecastHeadline').textContent = headlines[cat.name];
  document.getElementById('forecastSubline').textContent =
    `Based on Delhi's recent pollution trends, current weather conditions, and seasonal patterns from 5.5 years of historical data.`;

  document.getElementById('statLower').textContent = Math.round(data.AQI_lower_bound);
  document.getElementById('statUpper').textContent = Math.round(data.AQI_upper_bound);
  document.getElementById('confRange').textContent =
    `${Math.round(data.AQI_lower_bound)} – ${Math.round(data.AQI_upper_bound)}`;

  // Confidence fill — show spread relative to 500
  const spread = (data.AQI_upper_bound - data.AQI_lower_bound) / 500;
  const fill = Math.max(20, 100 - spread * 200);
  document.getElementById('confFill').style.width = `${fill}%`;
  document.getElementById('confFill').style.background = cat.color;

  // Health advice
  document.getElementById('healthIcon') && (document.getElementById('healthIcon').textContent = adv.icon);
  document.getElementById('healthText').textContent = adv.text;
  document.querySelector('.health-icon').textContent = adv.icon;

  // Chart
  await buildChart(aqi);
}

// ── CUSTOM FORECAST ──
async function runCustomForecast() {
  const get = id => parseFloat(document.getElementById(id).value);

  const aqi24  = get('inp_aqi24');
  const aqi48  = get('inp_aqi48');
  const aqi72  = get('inp_aqi72');
  const aqi168 = get('inp_aqi168');
  const temp   = get('inp_temp');
  const humid  = get('inp_humid');
  const wind   = get('inp_wind');
  const pm25   = get('inp_pm25');
  const pm10   = get('inp_pm10');

  if ([aqi24, aqi48, aqi72, aqi168, temp, humid, wind, pm25, pm10].some(isNaN)) {
    alert('Please fill in all fields before forecasting.');
    return;
  }

  const btnText = document.getElementById('btnText');
  const spinner = document.getElementById('btnSpinner');
  btnText.textContent = 'Calculating…';
  spinner.style.display = 'block';

  const rolling_mean = (aqi24 + aqi48 + aqi72) / 3;
  const rolling_max  = Math.max(aqi24, aqi48, aqi72);
  const rolling_min  = Math.min(aqi24, aqi48, aqi72);

  const payload = {
    AQI_lag_24h: aqi24, AQI_lag_48h: aqi48,
    AQI_lag_72h: aqi72, AQI_lag_168h: aqi168,
    AQI_lag_8760h: aqi168 * 1.1,
    AQI_rolling_mean_24h: rolling_mean,
    AQI_rolling_mean_48h: (rolling_mean + aqi168) / 2,
    AQI_rolling_std_24h: Math.abs(aqi24 - rolling_mean),
    AQI_rolling_max_24h: rolling_max,
    AQI_rolling_min_24h: rolling_min,
    "PM2.5": pm25, PM10: pm10,
    NO2: 55, CO: 2.0, SO2: 15, O3: 25,
    temperature_lag_24h: temp,
    humidity_lag_24h: humid,
    windspeed_lag_24h: wind,
    precipitation_lag_24h: 0,
    temperature_rolling_mean_24h: temp,
    humidity_rolling_mean_24h: humid,
    windspeed_rolling_mean_24h: wind,
    precipitation_rolling_mean_24h: 0,
    forecast_datetime: new Date().toISOString().slice(0,19).replace('T',' ')
  };

  try {
    const res = await fetch(`${API}/forecast`, {
      method: 'POST',
      headers: { 'Content-Type':'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    const aqi = Math.round(data.predicted_AQI);
    const cat = getCategory(aqi);
    const adv = getHealthAdvice(cat.name);

    document.getElementById('resultAQI').textContent = aqi;
    document.getElementById('resultCategory').textContent = cat.name;
    document.getElementById('resultCategory').style.color = cat.text;
    document.getElementById('resultRange').textContent =
      `Likely range: ${Math.round(data.AQI_lower_bound)} – ${Math.round(data.AQI_upper_bound)} AQI`;
    document.getElementById('resultAdvice').textContent = adv.text;
    document.getElementById('resultBanner').classList.add('show');

  } catch(e) {
    alert('Could not reach the API. It may be waking up — please try again in 30 seconds.');
  }

  btnText.textContent = 'Get Tomorrow\'s Forecast';
  spinner.style.display = 'none';
}

// ── CLOCK ──
function updateClock() {
  const now = new Date();
  document.getElementById('liveClock').textContent =
    now.toLocaleString('en-IN', {
      weekday:'short', day:'numeric', month:'short',
      hour:'2-digit', minute:'2-digit'
    });
}
setInterval(updateClock, 1000);
updateClock();

// ── INIT ──
loadDefaultForecast();
