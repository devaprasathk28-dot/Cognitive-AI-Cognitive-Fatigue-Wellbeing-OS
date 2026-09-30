import pandas as pd
import numpy as np
import torch
import torch.nn as nn

SEQ_LEN = 20

class FatigueLSTM(nn.Module):

    def __init__(self):
        super().__init__()

        self.lstm = nn.LSTM(
            input_size=2,
            hidden_size=32,
            num_layers=2,
            batch_first=True
        )

        self.fc = nn.Linear(32,1)

    def forward(self,x):

        out,_ = self.lstm(x)
        out = out[:,-1,:]

        return self.fc(out)


def load_data():

    df = pd.read_csv("data/fatigue_timeseries.csv")

    X=[]
    y=[]

    values = df[["fatigue_score","fatigue_momentum"]].values

    for i in range(len(values)-SEQ_LEN):

        X.append(values[i:i+SEQ_LEN])
        y.append(values[i+SEQ_LEN][0])

    return np.array(X),np.array(y)


def train():

    X,y = load_data()

    X=torch.tensor(X,dtype=torch.float32)
    y=torch.tensor(y,dtype=torch.float32)

    model = FatigueLSTM()

    optim = torch.optim.Adam(model.parameters(),lr=0.001)

    loss_fn = nn.MSELoss()

    for epoch in range(50):

        pred = model(X).squeeze()

        loss = loss_fn(pred,y)

        optim.zero_grad()

        loss.backward()

        optim.step()

        print("epoch",epoch,"loss",loss.item())

    torch.save(model.state_dict(),"models/fatigue_model.pt")


if __name__=="__main__":
    train()
