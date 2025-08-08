import torch.nn as nn    
class SimpleInformer(nn.Module):
    def __init__(self,input_dim,d_model=64,nhead=4,num_layers=2):
        super().__init__()
        self.input_proj=nn.Linear(input_dim,d_model)
        encoder_layer = nn.TransformerEncoderLayer(d_model=d_model,nhead=nhead)
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)

        self.output_proj = nn.Linear(d_model, 1)

    def forward(self, x):
        x = self.input_proj(x)
        x = x.permute(1, 0, 2)  
        x = self.transformer(x)
        return self.output_proj(x[-1])