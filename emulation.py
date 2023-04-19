import math
import typing as tp

import numpy as np

import generation 

from dataclasses import dataclass


@dataclass
class Position:
    token0: str
    token1: str
    sqrt_ratio_a: float
    sqrt_ratio_b: float
    liquidity: float
    liquidation_threshold: float
    borrow_threshold: float

        
def get_position_for_usd(
    token0: str,
    token1: str,
    sqrt_ratio_a: float,
    sqrt_ratio_b: float,
    usd_amount: float,
    price0: float,
    price1: float,
    liquidation_threshold: float,
    borrow_threshold: float,
) -> Position:
    ratio = math.sqrt(price0 / price1)
    ratio = max(sqrt_ratio_a, ratio)
    ratio = min(sqrt_ratio_b, ratio)
    liquidity_to_amount0 = (sqrt_ratio_b - ratio) / ratio / sqrt_ratio_b
    liquidity_to_amount1 = (ratio - sqrt_ratio_a)
    liquidity_price = liquidity_to_amount0 * price0 + liquidity_to_amount1 * price1
    return Position(
        token0=token0,
        token1=token1,
        sqrt_ratio_a=sqrt_ratio_a,
        sqrt_ratio_b=sqrt_ratio_b,
        liquidity=usd_amount / liquidity_price,
        liquidation_threshold=liquidation_threshold,
        borrow_threshold=borrow_threshold,
    )


class Vault:
    def __init__(
        self,
        tokens: tp.List[str],
        positions: tp.Optional[tp.List[Position]] = None,
        debt: float = 0.,
    ):
        self.debt = debt
        self.tokens = tokens
        self.positions = positions or []
    
    def deposit_collateral(self, position: tp.List[Position]):
        self.positions.append(position)
        
    def calculate_collateral(self, prices: np.array) -> tp.Tuple[np.array, np.array, np.array]:
        adjusted = np.zeros(prices.shape[1], dtype='float32')
        max_borrow = np.zeros(prices.shape[1], dtype='float32')
        actual = np.zeros(prices.shape[1], dtype='float32')
        for position in self.positions:
            price0 = prices[self.tokens.index(position.token0)]
            price1 = prices[self.tokens.index(position.token1)]
            ratio = np.sqrt(price0 / price1)
            ratio = np.maximum(ratio, position.sqrt_ratio_a)
            ratio = np.minimum(ratio, position.sqrt_ratio_b)
            amount0 = position.liquidity * (position.sqrt_ratio_b - ratio) / ratio / position.sqrt_ratio_b
            amount1 = position.liquidity * (ratio - position.sqrt_ratio_a)
            price = amount0 * price0 + amount1 * price1
            actual += price
            adjusted += price * position.liquidation_threshold
            max_borrow += price * position.borrow_threshold
        return adjusted, actual, max_borrow
    
    def health_factor(self, prices: np.array) -> np.array:
        (adjusted, _, _) = self.calculate_collateral(prices)
        return adjusted / self.debt
    
    def liquidation_earnings(
        self,
        prices: np.array,
        liquidator_premium: float,
        protocol_premium: float,
    ) -> np.array:
        (adjusted, actual, _) = self.calculate_collateral(prices)
        to_repay = actual * (1 - liquidator_premium)
        to_repay = np.maximum(to_repay, self.debt)
        protocol_earning = actual * protocol_premium
        protocol_earning = np.minimum(protocol_earning, actual - to_repay)
        return actual - to_repay, protocol_earning
        
    def charge_fees(self, fee: float):
        self.debt *= 1 + fee


class Emulation:
    def __init__(
        self,
        vaults: tp.List[Vault],
        feed: generation.PriceFeed,
        liquidation_costs: np.array,
        fee: float,
        liquidation_premium: float,
        protocol_premium: float,
    ):
        self.vaults = vaults
        self.price_feed = feed
        self.liquidation_costs = liquidation_costs
        self.is_liquidated = np.zeros((len(vaults), feed.current_state.shape[1]), dtype='bool')
        self.fee = fee
        self.liquidation_premium = liquidation_premium
        self.protocol_premium = protocol_premium
        self.charged_fees = np.zeros(len(vaults), dtype='float32')
        self.losses = np.zeros((len(vaults), feed.current_state.shape[1]), dtype='float32')
    
    def health_factor(self):
        result: tp.List[np.array] = []
        for vault in self.vaults:
            result.append(vault.health_factor(self.price_feed.prices).reshape((1, -1)))
        return np.vstack(result)
    
    def next_step(self):
        self.price_feed.next_step()
        for i, vault in enumerate(self.vaults):
            old_debt = vault.debt
            vault.charge_fees(self.fee)
            self.charged_fees[i] += vault.debt - vault.debt

    def liquidate(self):
        to_liquidate = (self.health_factor() < 1) & (~self.is_liquidated)
        for i, vault in enumerate(self.vaults):
            liquidator_earnings, protocol_earnings = vault.liquidation_earnings(
                self.price_feed.prices,
                self.liquidation_premium,
                self.protocol_premium,
            )
            mask = to_liquidate[i] & (liquidator_earnings > self.liquidation_costs[i])
            self.losses[i][mask] = -protocol_earnings[mask] - self.charged_fees[i]
            self.is_liquidated[i] |= mask 
            
    def check_undercollateralized(self):
        to_liquidate = (self.health_factor() < 1) & (~self.is_liquidated)
        for i, vault in enumerate(self.vaults):
            liquidator_earnings, protocol_earnings = vault.liquidation_earnings(
                self.price_feed.prices,
                self.liquidation_premium,
                self.protocol_premium,
            )
            mask = to_liquidate[i] & (liquidator_earnings <= self.liquidation_costs[i])
            self.losses[i][mask] = self.liquidation_costs[i] - protocol_earnings[mask] - self.charged_fees[i] - liquidator_earnings[i]
            self.is_liquidated[i] |= mask 