You are generating a deterministic frontend UI for an existing backend system.

You must not invent backend functionality.

You must only call the endpoints described below.

SYSTEM CONTEXT

This project is an ML A/B testing framework backend built with FastAPI.

The backend already exists and must not be modified.

The frontend must interact with these API endpoints.

GET /health

POST /api/v1/predict

POST /api/v1/outcomes

GET /api/v1/experiments/{experiment_id}/results

The system routes prediction requests between two ML models and records outcomes.

The backend computes statistical comparisons between model variants.

The results endpoint returns:

* mean outcome for model A
* mean outcome for model B
* difference in means
* confidence interval
* sample size per variant

TECHNICAL REQUIREMENTS

Generate a Next.js dashboard application.

Use:

Next.js 14
React
TypeScript
TailwindCSS
shadcn/ui components
Recharts for charts

The UI must be clean and look like a SaaS analytics product.

The layout must include a sidebar navigation.

PAGES REQUIRED

Dashboard

Show summary cards:

total experiments
total predictions
total outcomes

Experiment Results Page

User enters experiment_id.

Call:

GET /api/v1/experiments/{experiment_id}/results

Display:

mean outcome model A
mean outcome model B
difference in means

Charts:

bar chart comparing means
confidence interval visualization

Prediction Page

Form fields:

experiment_id
JSON features

Call:

POST /api/v1/predict

Display returned:

request_id
model_variant
prediction

Outcome Reporting Page

Form fields:

request_id
value

Call:

POST /api/v1/outcomes

Display success confirmation.

RULES

Do not invent backend endpoints.

Do not simulate backend data.

Use fetch() to call the API.

All API base URLs must be configurable via environment variable:

NEXT_PUBLIC_API_BASE_URL
