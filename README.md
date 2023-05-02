# Risk-Sensitive Parameter Selection for CDP Module

## Overview

In this repository we are testing the cdp module parameters to determine, if they are safe enough. This CDP module simulation uses the Geometrical Brownian motion to emulate token price movements. This model assumes that the price of the token moves randomly over time, with its future value being determined by its past values. It also incorporates a "jump" concept inspired by DAI risk estimation, which introduces sudden and unpredictable shifts in the token price.

It's important to note that this simulation does not take into consideration side effects during the liquidation process, such as liquidity insufficiency or pressure on prices.

## Price Movement Parameters

The parameters for the Geometrical Brownian motion have been chosen based on the data from 2023-03-16 to 2023-04-05. The jump parameters have been configured manually based on the risk estimation of the token.

## Structure

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

After configuring these parameters you can run `emulation.ipynb` notebook to validate them. The simulation outputs the CDP metrics, including the VaR at 0.1%, which determines if the parameter set is acceptable.

Stabilization fees, protocol premium on liquidation and liquidators premium can be configured directly in the `emulation.ipynb` notebook
