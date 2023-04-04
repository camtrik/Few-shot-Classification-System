import torch
import torchvision
from model.prototype import protoNetDemo

def predict_(sample, present_model):
    model = protoNetDemo()

    state_dict = torch.load(present_model)
    model.load_state_dict(state_dict)
    loss, output = model.set_forward_loss(sample)
    return loss, output
