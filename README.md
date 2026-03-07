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

# Example Output

Example simulation result (illustrative):

Expected disruption exposure: €380,000  
P50 exposure: €420,000  
P95 worst-case exposure: €1,050,000  

Mitigation scenario savings: 5–8%

These numbers demonstrate how simulation outputs help operations teams evaluate disruption decisions.

---

# Architecture Overview

Passenger Impact Engine uses a modular architecture designed for reproducible simulation and analytical workflows.

Core components:

Client / API Request  
↓  
FastAPI Backend  
↓  
Simulation Engine (Python Monte Carlo models)  
↓  
Event Store / Data Layer  
↓  
Risk Analytics Output (reports, dashboards)

Key architectural concepts:

- Monte Carlo simulation engine
- Event-sourced data model (CQRS-style workflow)
- API-driven simulation execution
- Docker-based reproducible environments

---

# Tech Stack

- Python
- FastAPI
- PostgreSQL
- Docker
- Monte Carlo Simulation
- Event-driven architecture (CQRS)

---

# Repository Structure
