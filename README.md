# FleetGuard AI

FleetGuard AI is a predictive maintenance capstone project for commercial vehicles.

The application combines synthetic fleet data, machine learning, configurable failure-scoring rules, Remaining Useful Life estimation, FastAPI services, a React dashboard, and an AI Insight Agent.

## Project Objective

The objective is to convert vehicle telematics and historical component failures into:

* Failure probability scores
* Green / Amber / Red risk tiers
* Top contributing telematics signals
* Probability trends
* Remaining Useful Life estimates
* Natural-language fleet insights through an AI agent

## Architecture

```text
Synthetic Fleet Data
        |
        v
SQLite Database
        |
        v
Correlation / Logistic Regression
        |
        v
ML-derived Signal Weights
        |
        v
Rule Builder
        |
        v
Failure Probability Scoring
        |
        +-------------------+
        |                   |
        v                   v
RUL Estimator         Insight Agent
        |                   |
        +---------+---------+
                  |
                  v
             FastAPI
                  |
                  v
             React UI
```

## Technology Stack

### Backend

* Python
* FastAPI
* SQLAlchemy
* SQLite
* pandas
* NumPy
* scikit-learn
* OpenAI API

### Frontend

* React
* Vite
* Axios
* CSS

### Testing

* pytest
* FastAPI TestClient
* httpx

## Dataset

The project uses a reproducible synthetic dataset.

Current dataset size:

* 400 vehicles
* 4 monitored parts
* 52 weeks of telematics per vehicle
* 20,800 telematics records
* 200 historical failure records

### Monitored Parts

| Part Code | Part           |
| --------- | -------------- |
| ELC-0152  | Alternator     |
| BAT-0201  | Battery        |
| CLG-0310  | Cooling Pump   |
| BRK-0412  | Brake Assembly |

## Telematics Signals

The system currently uses the following weekly telematics signals:

* Coolant temperature variance
* Oil pressure dips
* Battery voltage sag
* DTC recurrence rate
* Harsh braking frequency
* Overload duty share
* High-RPM dwell time
* Short-trip ratio
* Idle-time percentage

## Synthetic Data Generation

The synthetic dataset is generated using:

```text
backend/scripts/generate_data.py
```

The generator creates intentional relationships between telematics signals and component failure risk.

For example:

* Alternator failures are influenced by battery voltage sag, coolant temperature variance and operating stress.
* Brake Assembly failures are strongly influenced by harsh braking and overload duty.
* Cooling Pump failures are influenced by coolant-temperature behavior and high-RPM usage.

Run:

```powershell
python scripts\generate_data.py
```

## Correlation Analysis

Correlation analysis is performed using:

```text
backend/scripts/analyze_data.py
```

Run:

```powershell
python scripts\analyze_data.py
```

This verifies that historical failure events have measurable relationships with telematics signals.

## Machine Learning

Logistic Regression is used as the primary interpretable machine-learning model.

The prediction target represents whether a component failure occurs within an 8-week prediction window.

Model training:

```powershell
python scripts\train_model.py
```

Model evaluation:

```powershell
python scripts\evaluate_model.py
```

### Model Evaluation

Observed ROC-AUC scores were approximately:

| Component      | ROC-AUC |
| -------------- | ------: |
| Alternator     |   0.685 |
| Battery        |   0.732 |
| Cooling Pump   |   0.702 |
| Brake Assembly |   0.932 |

The dataset is highly imbalanced, so recall and ROC-AUC are more informative than accuracy alone.

## Rule Builder

Logistic Regression coefficients are converted into interpretable signal weights.

Positive coefficients are normalized into configurable risk weights.

Rules are persisted in:

```text
rule_config
```

Generate and persist the rules using:

```powershell
python scripts\build_rules.py
```

Users can enable or disable signals from the React Rule Builder without retraining the model.

The scoring engine automatically renormalizes the active signal weights.

## Failure Probability Scoring

The scoring engine combines:

```text
Normalized signal value
        ×
ML-derived signal weight
        =
Signal contribution
```

The signal contributions are combined into a failure-risk percentage.

### Risk Tiers

* Green: below 40%
* Amber: 40% to below 70%
* Red: 70% and above

For each VIN and part, the application provides:

* Failure probability
* Risk tier
* Top contributing signals
* Current telematics values
* Recent probability trend

## Remaining Useful Life

The RUL estimator considers:

* Component design life
* Current vehicle mileage
* Previous component replacement history
* Current component mileage
* Failure probability
* Estimated degradation severity

The output contains:

* Remaining kilometres
* Estimated remaining days
* Component replacement status
* Current component mileage
* Service recommendation

## Insight Agent

FleetGuard includes an AI Insight Agent with tool access to the same backend services used by the dashboard.

The agent can answer questions such as:

```text
What parts are monitored?

Which vehicles have the highest alternator failure risk?

Which vehicles are Red tier for the Brake Assembly?

Why is VIN FG000216 at risk for its alternator?

What is the remaining useful life of the alternator in FG000216?
```

The agent is instructed to use backend tool results rather than inventing fleet values.

## Backend API

Main API endpoints include:

```text
GET  /parts

GET  /rules/{part_code}
PUT  /rules/{part_code}

GET  /predictions/{part_code}

GET  /predictions/{vin}/{part_code}

GET  /rul/{vin}/{part_code}

POST /agent/query
```

Interactive API documentation is available while the backend is running at:

```text
http://127.0.0.1:8000/docs
```

## Frontend Features

The React frontend currently includes:

### Failure Probability

* Part selection
* Ranked VIN list
* Failure probability
* Risk tier
* Top contributing signal

### Rule Builder

* Part selection
* ML-derived weights
* Signal include/exclude control
* Persisted rule configuration

### Vehicle Risk Detail

* Failure probability
* Risk tier
* Top contributing signals
* Current telematics
* Probability trend
* RUL
* Service recommendation

### Insight Agent

A persistent chat panel allows users to ask fleet-related questions while viewing dashboard data.

## Project Structure

```text
FleetGuard-AI/
|
├── backend/
|   ├── app/
|   |   ├── agents/
|   |   ├── api/
|   |   ├── services/
|   |   ├── database.py
|   |   ├── models.py
|   |   └── main.py
|   |
|   ├── scripts/
|   |   ├── generate_data.py
|   |   ├── analyze_data.py
|   |   ├── train_model.py
|   |   ├── evaluate_model.py
|   |   └── build_rules.py
|   |
|   ├── tests/
|   ├── requirements.txt
|   └── fleetguard.db
|
├── frontend/
|   ├── src/
|   |   ├── pages/
|   |   ├── services/
|   |   ├── App.jsx
|   |   ├── App.css
|   |   └── index.css
|   |
|   └── package.json
|
├── docs/
└── README.md
```

## Running the Backend

Navigate to:

```powershell
cd D:\training-26\FleetGuard-AI\backend
```

Activate the virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Start FastAPI:

```powershell
uvicorn app.main:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

## Running the Frontend

Open another terminal:

```powershell
cd D:\training-26\FleetGuard-AI\frontend
```

Run:

```powershell
npm run dev
```

Frontend:

```text
http://localhost:5173
```

## Running Tests

From the backend directory with the virtual environment activated:

```powershell
pytest
```

The tests validate:

* API health
* Parts API
* Rule API
* Prediction API
* Invalid-part handling
* Risk-tier logic
* Signal normalization

## Environment Variables

Create:

```text
backend/.env
```

Example:

```text
OPENAI_API_KEY=your_api_key
OPENAI_MODEL=your_model_name
```

Do not commit `.env` to Git.

The `.gitignore` should include:

```text
.env
.venv/
__pycache__/
*.pyc
```

## Capstone Deliverables Covered

The project currently demonstrates:

* Reproducible synthetic data generation
* Documented relational schema
* Correlation analysis
* Machine-learning model
* Model evaluation
* Configurable Rule Builder
* Fleet-wide failure scoring
* VIN-level explanation
* Failure probability trends
* Remaining Useful Life estimation
* REST APIs
* React frontend
* Tool-calling AI Insight Agent
* Automated backend tests

## Future Improvements

Possible future enhancements include:

* Time-based ML validation
* Probability calibration
* Threshold optimization
* More realistic component installation history
* Improved RUL regression model
* Additional fleet components
* Model monitoring
* Authentication and user roles
* PostgreSQL deployment
* Cloud deployment
* Optional Action Agent for service-message drafting

## Disclaimer

FleetGuard AI is an educational capstone prototype built on synthetic data.

Its predictions should not be used for real vehicle maintenance or safety decisions.
