# Passenger Impact Engine (PIE)

Monte Carlo Airline Disruption Risk Simulation Platform

Passenger Impact Engine (PIE) is a simulation system designed to estimate airline disruption costs and EU261 passenger compensation exposure using Monte Carlo modeling.

The platform simulates thousands of disruption scenarios such as delays, cancellations, and denied boarding to estimate financial risk and operational exposure.

PIE helps airline operations and finance teams answer:

> If Flight X is delayed or cancelled today, what is our expected passenger compensation exposure — and how severe could the worst-case outcome be?

---

# Problem

Airline disruptions create significant financial risk due to passenger compensation regulations such as **EU261**.

Operational teams often lack fast analytical tools to estimate:

- expected compensation exposure
- worst-case disruption costs
- mitigation scenario impact

Passenger Impact Engine addresses this problem by combining **simulation modeling** with **backend analytics systems**.

---

# Key Features

- Monte Carlo simulation of airline disruption scenarios
- EU261 passenger compensation exposure forecasting
- Risk distribution outputs (Expected value, P50, P95)
- Scenario comparison for mitigation strategies
- Event-sourced architecture tracking ticket lifecycle
- FastAPI backend exposing simulation APIs
- Dockerized environment for reproducible deployment
- Executive-ready analytical outputs

---

## Tech Stack

- Python
- FastAPI
- PostgreSQL
- Docker
- Monte Carlo simulation
- Event-driven architecture (CQRS)

  ## System Architecture

The platform follows a modular backend architecture designed for scalable simulation workloads.

Client / API Request
        │
        ▼
FastAPI Backend
        │
        ▼
Monte Carlo Simulation Engine
        │
        ▼
Event Store (PostgreSQL)
        │
        ▼
Risk Analytics Output
(Dashboard + Reports)

## Quick Start

Clone the repository:

git clone https://github.com/salehmahamathissene/passenger-impact-engine

Run with Docker:

docker compose up --build

Open the dashboard:

http://localhost:8000

Why This Matters

Airline disruptions cost billions of euros annually. 
Passenger compensation regulations such as EU261 create significant financial exposure.

Passenger Impact Engine allows airlines to simulate disruption scenarios and evaluate 
operational decisions before they are taken.

The goal is to help operations teams reduce disruption cost and improve operational resilience.

# Example Output

Example simulation result (illustrative):

Expected disruption exposure: €380,000  
P50 exposure: €420,000  
P95 worst-case exposure: €1,050,000  

Mitigation scenario savings: 5–8%

These numbers demonstrate how simulation outputs help operations teams evaluate disruption decisions.

---

Client / API Request
        │
        ▼
FastAPI Backend
        │
        ▼
Simulation Engine (Monte Carlo Models)
        │
        ▼
Event Store / Data Layer
        │
        ▼
Risk Analytics Output (Reports & Dashboard)

## Example Scenario

Flight: Paris → Madrid  
Passengers: 180  
Delay: 3h 20m  

Under EU261 regulations, passengers may be eligible for €250 compensation.

Simulation result (10,000 scenarios):

Expected exposure: €42,500  
P50: €45,000  
P95 worst case: €82,000  

Operational decision comparison:

Delay aircraft swap → exposure €42k  
Cancel flight → exposure €71k  

Estimated savings from mitigation: 40%

## Roadmap

Planned improvements:

- integration with real flight schedule datasets
- crew repositioning cost modeling
- real-time disruption simulation
- machine learning delay prediction
- advanced risk visualization dashboard
