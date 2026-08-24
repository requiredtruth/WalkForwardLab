# Project specification

WalkForwardLab measures a small strategy grid on historical close data. Each fold selects parameters only from prior training observations, skips an explicit embargo, and then freezes those parameters for a non-overlapping test window. Positions use information available at a bar close and apply only to the following return.

The project never downloads data, predicts future returns, places orders, connects to accounts, or converts historical measurements into claims of profitability.
