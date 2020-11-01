import torch.nn.functional as F
import torch
from parse_config import ConfigParser
import torch.nn as nn
import pdb

#일단 softhinge만 사용하는 거로
def partial_opt(loss_value, threshold):
    L = 0
    batch_size = len(loss_value)
#     v_set = torch.nn.Parameter(data=torch.ones(batch_size), requires_grad=False)
    # v_set = torch.ones(batch_size)
    sorted_loss, index = torch.sort(loss_value) #Sort losses in non-dereasing order
    index_list = []
    for i in range(batch_size):
        L += sorted_loss[i]
        if L <= (threshold + 1 - i):
            index_list.append(index[i].item())
                
    return index_list

def softHingeLoss(margin, output, target): #margin.shape = [batch_size]
    
    fst_term = F.relu(1 - margin)
    snd_term = F.relu(1 - output[range(len(output)), target] + torch.logsumexp(output, dim=1))
    soft_hinge_loss = torch.where(margin >= 0, fst_term, snd_term)


    return soft_hinge_loss

def hardHingeLoss(margin): # margin.shape = [batch_size]
    
    hard_hinge_loss = 1 - margin
    hard_hinge_loss[hard_hinge_loss < 0] = 0

    return hard_hinge_loss


class Binary(nn.Module):
    def __init__(self):
        super().__init__() # init the base class
        
    def forward(self, x):
        
        return torch.ones_like(x)


class NPCLoss(nn.Module):	
    def __init__(self, epsilon):	   
        super().__init__()	
        self.epsilon = epsilon	

    def forward(self, output, target):	
        # set base loss function	
#         base_loss = SoftHingeLoss()
        
        # margin for each data point = t_y - max(i!=y)t_i ; y is target class num, shape (Batch_size,)
        target = target.long()
        # output = F.softmax(output, dim=1)
        values, indices = torch.topk(output, k=2, dim=1)
        margin1 = output[range(len(output)), target] - values[:, 0]
        margin2 = output[range(len(output)), target] - values[:, 1]
        margin = torch.where(margin1 != 0, margin1, margin2)
        
        #calculate threshold
        batch_size = output.shape[0]
        threshold = ((1 - self.epsilon) ** 2) * batch_size + (1 - self.epsilon) * torch.sum(margin < 0.)
         #threshold 왜 int???
        
        # parameters required to calculate NPCL
        loss_val = softHingeLoss(margin, output, target).to('cuda')
        v_index = partial_opt(loss_val, threshold) #.to('cuda')

        # calculate NPCL
        npcl_1 = torch.sum(loss_val[v_index]).to('cuda')
        bi = Binary()
        npcl_2 = threshold - torch.sum(bi(loss_val[v_index])).to('cuda')
        npcl_2.requires_grad=True
        
        loss_final = torch.max(npcl_1, npcl_2)# npcl_2 if npcl_1 < npcl_2 else npcl_1
        
        return loss_final /  len(v_index)
    
class CLoss(nn.Module):
    def __init__(self):
        super().__init__()
    
    def forward(self, output, target):
        
        # margin for each data point = t_y - max(i!=y)t_i , y is target class num, shape (Batch_size,)
        prob_output = F.softmax(output, dim=1)
        target = target.long()
        # tmp_output[:, target] = float("-inf")
        margin = prob_output[:, target] - torch.max(prob_output, dim=1).values
        
        # parameters required to calculate curriculum loss
        batch_size = output.shape[0]
        l = softHingeLoss(margin, output, target).to('cuda') # shape = [batch]
        threshold = batch_size # temporarily set to n; it should be 0 <= C <= 2n
        v = partial_opt(l, threshold)# .to('cuda') # shape = [batch] / 0 or 1
        
        # curriculum loss is maximum value between loss 1 and 2
        curriculum_loss_1 = torch.dot(v, l)
        curriculum_loss_2 = batch_size - torch.sum(v) + torch.sum(torch.ones(batch_size)[margin < 0])
        
        return curriculm_loss_2 if curriculm_loss_1 < curriculum_loss_2 else curriculm_loss_1
    
class Tight_CLoss(nn.Module):
    def __init__(self):
        super().__init__()
    
    def forward(self, output, target):
        # margin for each data point = t_y - max(i!=y)t_i , y is target class num, shape (Batch_size,)
        tmp_output = output.clone()
        target = target.long()
        tmp_output[range(len(output)), target] = float("-inf")
        margin = output[range(len(output)), target] - torch.max(tmp_output, dim=1).values
        
        # parameters required to calculate curriculum loss
        l = softHingeLoss(margin) # shape = [batch]
        v = partial_opt(l, threshold) # shape = [batch] / 0 or 1
        batch_size = output.shape[0]
        
        # curriculum loss is maximum value between loss 1 and 2
        curriculum_loss_1 = torch.dot(v, l)
        curriculum_loss_2 = batch_size - torch.sum(v)
        
        return curriculm_loss_2 if curriculm_loss_1 < curriculum_loss_2 else curriculm_loss_1
    
