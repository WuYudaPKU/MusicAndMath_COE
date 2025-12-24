import torch
import torch.nn as nn
import math

class MelodyTransformer(nn.Module):
    def __init__(self, vocab_size,d_model=128,nhead=4,num_layers=3):
        super().__init__()
        self.embedding=nn.Embedding(vocab_size, d_model)
        self.pos_encoder=nn.Parameter(torch.zeros(1,128,d_model)) 
        decoder_layer=nn.TransformerEncoderLayer(d_model=d_model,nhead=nhead,batch_first=True)
        self.transformer=nn.TransformerEncoder(decoder_layer,num_layers=num_layers)
        self.fc_out=nn.Linear(d_model, vocab_size)

    def forward(self,x,mask=None):
        x=self.embedding(x)*math.sqrt(x.size(-1))
        x=x+self.pos_encoder[:,:x.size(1),:]
        output=self.transformer(x,mask=mask)
        return self.fc_out(output)