import typing as tp

import numpy as np


def extract_params(prices: np.array) -> tp.Tuple[np.array, np.array]:
    """
    Extract parameters for Geometrical Brownian motion emulation
    
    Args:
        prices: 2-D array with shape (n_tokens, n_measurements)
        
    Returns:
        means: 1-D array with shape (n_tokens,)
        covariations: 2-D array with shape (n_tokens, n_tokens)
    """
    diffs = np.diff(np.log(prices), axis=1)
    return np.mean(diffs, axis=1), np.cov(diffs)


class PriceFeed:
    def __init__(
        self,
        means: np.array,
        covariations: np.array,
        starting_values: np.array,
        jumps: tp.List[np.array],
        jump_probs: tp.List[np.array],
        recovery: tp.List[int],
        n_samples: int = 100,
    ):
        self.means = means
        self.covariations = covariations
        self.current_state = np.vstack([np.ones((1, n_samples), dtype='float32') * value for value in starting_values])
        self.recovery_clock = np.zeros((len(means), n_samples), dtype='int32')
        self.last_jump = np.zeros((len(means), n_samples), dtype='float32')
        self.jumps = jumps
        self.jump_probs = jump_probs
        self.recovery = recovery
        
    @property
    def prices(self):
        return np.vstack([np.ones((1, self.current_state.shape[1])), self.current_state])

    def next_step(self):
        generated = np.random.multivariate_normal(self.means, self.covariations, size=self.current_state.shape[1]).T
        jump_values = np.vstack([
            np.random.choice(j, size=(1, self.current_state.shape[1]), p=p) for j, p in zip(self.jumps, self.jump_probs)
        ])
        recovery_mask = self.recovery_clock > 0
        jump_values[recovery_mask] = 1
        generated -= self.last_jump / np.maximum(1, self.recovery_clock)
        self.last_jump -= self.last_jump / np.maximum(1, self.recovery_clock)
        self.recovery_clock[recovery_mask] -= 1
        self.last_jump[recovery_mask & (self.recovery_clock == 0)] = 0
        for i in range(len(jump_values)):
            self.recovery_clock[i][jump_values[i] < 1] = self.recovery[i]
        for xi, mi, vi in zip(self.last_jump, jump_values < 1, jump_values):
            xi[mi] = np.log(vi[mi])
        self.current_state = self.current_state * np.exp(generated) * jump_values