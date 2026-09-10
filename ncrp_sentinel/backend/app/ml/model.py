import torch
import torch.nn as nn

class ATMTrajectoryLSTM(nn.Module):
    """
    PyTorch 2-layer LSTM model for predicting ATM cashout coordinate trajectories
    based on digital fraud hops (amount, time/hour, city, state, bank).
    """
    def __init__(self, input_dim: int = 5, hidden_dim: int = 128):
        super(ATMTrajectoryLSTM, self).__init__()
        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=2,
            batch_first=True,
            dropout=0.2
        )
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 2)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x shape: (batch_size, seq_len, input_dim)
        _, (hn, _) = self.lstm(x)
        # hn[-1] shape: (batch_size, hidden_dim)
        return self.fc(hn[-1])
