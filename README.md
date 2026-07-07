# Marketing Measurement Triangulation: MMM, MTA & Incrementality Testing

> 🚧 **Work in Progress** — This project is currently under active development.

## Overview
This project explores how accurately three marketing measurement methods — Multi-Touch Attribution (MTA), Marketing Mix Modeling (MMM), and Incrementality Testing — estimate the true causal impact of advertising channels.

A synthetic e-commerce dataset with predefined ground truth will be used to benchmark each method and quantify where and why they diverge from real incremental lift.

## What's Coming
- Synthetic dataset generation with known incremental lift per channel
- MTA: Markov chain & Shapley value attribution
- MMM: Ridge regression with adstock & saturation transformations
- Incrementality: geo-based holdout test via diff-in-diff
- Benchmarking all three methods against ground truth
- Interactive Streamlit dashboard with a practical method-selection framework

## Stack
Python · pandas · numpy · scipy · statsmodels · scikit-learn · pycausalimpact · matplotlib · seaborn · plotly · streamlit
