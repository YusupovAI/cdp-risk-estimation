# Risk-Sensitive Parameter Selection for CDP Module

## Overview

The main parts are following:

1. `collection.ipynb`: This notebook is used for collecting historical data, such as asset prices.

2. `parameters.ipynb`: This notebook is used for extracting distribution parameters from the collected historical data. The main metrics are price volatility and trend. Moreover, some EDA about prices can be found here

3. `emulation.ipynb`: This notebook is used for emulating market conditions using Geometric Brownian Motion based on the estimated distribution parameters.

4. `min_width.ipynb`: This notebook is used for estimating the minimum width parameter, which is not risk-sensitive, but is needed for stable liquidations without upfront liquidity.

These Jupyter notebooks provide a comprehensive workflow for risk-sensitive parameter selection in a CDP module, taking into account historical data, distribution parameters, price emulation and liquidations. They serve as a powerful tool for data-driven and informed decision-making in managing the risk of a CDP module in a blockchain-based system.

## How to use

There are some things, that can be configured via `config.json`. They are following:

1. Vaults to use in the emulation

2. Liquidation thresholds

3. Borrow thresholds

After configuring these parameters you can run `emulation.ipynb` notebook to validate them.

Stabilization fees, protocol premium on liquidation and liquidators premium can be configured directly in the `emulation.ipynb` notebook
