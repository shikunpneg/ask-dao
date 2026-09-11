# On the Stability of Recursive Estimators under Noisy Channels

## Abstract
We study how an AGM-style belief revision process behaves when observations arrive
through a noisy channel. The model always converges to the true hypothesis when the
channel quality is estimated correctly. However, when the agent underestimates the noise,
the posterior remains biased. It remains unclear whether this bias can be eliminated by
collecting more evidence.

## 1. Introduction
Prior work assumes the noise level is known. This assumption is violated in practice.
Our goal is to characterize the bias as a function of channel capacity.

## 2. Results
Theorem 1. For every correct model the posterior converges to the true state for all
channel capacities above a threshold. The critical sample size grows monotonically with
the estimated noise level. We observe that the bias is bounded by the channel capacity.
This upper bound is tight in the low-capacity regime. An open problem is whether the
threshold depends on the prior. Future work should relax the i.i.d. assumption.
Conflicting evidence from the reinforcement learning literature suggests that agents
may instead collapse to a no-learning fixed point; whereas our analysis predicts smooth
degradation. 我们尚未解决的是：这种崩溃是否存在临界值，以及该临界值是否与先验相关。

## 3. Conclusion
Estimation error, not evidence scarcity, is the dominant failure mode.
