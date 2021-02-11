from torch.utils.data import Dataset, DataLoader
import torchvision.transforms as transforms
import random
import numpy as np
from PIL import Image
import json
import torch

class clothing_dataset(Dataset): 
    def __init__(self, root, transform, mode, num_samples=0, pred=[], probability=[], paths=[], num_class=14, refinement=None, train_imgs=None, teacher_idx=None, truncate_mode=None): 
        
        self.root = root
        self.transform = transform
        self.mode = mode
        self.train_labels = {}
        self.test_labels = {}
        self.val_labels = {}   
        
        self.refinement = refinement
        
        with open('%s/annotations/noisy_label_kv.txt'%self.root,'r') as f:
            lines = f.read().splitlines()
            for l in lines:
                entry = l.split()           
                img_path = '%s/'%self.root+entry[0][7:]
                self.train_labels[img_path] = int(entry[1])                         
        with open('%s/annotations/clean_label_kv.txt'%self.root,'r') as f:
            lines = f.read().splitlines()
            for l in lines:
                entry = l.split()           
                img_path = '%s/'%self.root+entry[0][7:]
                self.test_labels[img_path] = int(entry[1])   

        if mode == 'all':
            train_imgs=[]
            with open('%s/annotations/noisy_train_key_list.txt'%self.root,'r') as f:
                lines = f.read().splitlines()
                for l in lines:
                    img_path = '%s/'%self.root+l[7:]
                    train_imgs.append(img_path)                                
            random.shuffle(train_imgs)
            class_num = torch.zeros(num_class)
            self.train_imgs = []
            for impath in train_imgs:
                label = self.train_labels[impath] 
                if class_num[label]<(num_samples/14) and len(self.train_imgs)<num_samples:
                    self.train_imgs.append(impath)
                    class_num[label]+=1
                if len(self.train_imgs) >= num_samples:
                    break
            random.shuffle(self.train_imgs)       
        elif self.mode == "labeled":   
            train_imgs = paths 
            pred_idx = pred.nonzero()[0]
            if truncate_mode=='initial':
                pred_idx = list(set(pred_idx.tolist()) & set(teacher_idx.tolist()))
                pred_idx = torch.tensor(pred_idx)
            self.train_imgs = [train_imgs[i] for i in pred_idx]                
            self.probability = [probability[i] for i in pred_idx]            
            print("%s data has a size of %d"%(self.mode,len(self.train_imgs)))
        elif self.mode == "unlabeled":  
            train_imgs = paths 
            pred_idx = (1-pred).nonzero()[0]
            if truncate_mode == 'initial':
                whole_idx = list(range(len(paths)))
                pred_idx = pred_idx.tolist()
                teacher_idx = teacher_idx.tolist()
                tmp_set = set(whole_idx) - set(teacher_idx)
                tmp_set = tmp_set | set(pred_idx)
                pred_idx = torch.tensor(list(tmp_set))
            self.train_imgs = [train_imgs[i] for i in pred_idx]                
            self.probability = [probability[i] for i in pred_idx]            
            print("%s data has a size of %d"%(self.mode,len(self.train_imgs)))
            
        elif self.mode == 'labeled_svd':
            train_imgs = paths
            if self.refinement:
                pred_idx = pred.nonzero()[0]
                pred_idx_set = set(pred_idx.tolist())
                teacher_idx_set = set(teacher_idx.tolist())
                pred_idx = torch.tensor(list(pred_idx_set & teacher_idx_set))
            else:
                pred_idx = teacher_idx
                probability = torch.ones(len(paths),)
            self.train_imgs = [train_imgs[i] for i in pred_idx]                
            self.probability = [probability[i] for i in pred_idx]            
            print("%s data has a size of %d"%(self.mode,len(self.train_imgs)))
        elif self.mode == "unlabeled_svd":  
            train_imgs = paths 
            if self.refinement:
                clean_pred_idx = pred.nonzero()[0]
                clean_pred_idx_set = set(clean_pred_idx.tolist())
                teacher_idx_set = set(teacher_idx.tolist())
                all_idx_set = set(range(len(paths)))
                pred_idx = torch.tensor(list(all_idx_set - (clean_pred_idx_set & teacher_idx_set)))
            else:
                pred_idx = torch.arange(0, len(paths))
                pred_idx_set = set(pred_idx.tolist()) - set(teacher_idx.tolist())
                pred_idx = torch.tensor(list(pred_idx_set))    
            self.train_imgs = [train_imgs[i] for i in pred_idx]                
            self.probability = [probability[i] for i in pred_idx]            
            print("%s data has a size of %d"%(self.mode,len(self.train_imgs)))       
                
        elif mode=='test':
            self.test_imgs = []
            with open('%s/annotations/clean_test_key_list.txt'%self.root,'r') as f:
                lines = f.read().splitlines()
                for l in lines:
                    img_path = '%s/'%self.root+l[7:]
                    self.test_imgs.append(img_path)            
        elif mode=='val':
            self.val_imgs = []
            with open('%s/annotations/clean_val_key_list.txt'%self.root,'r') as f:
                lines = f.read().splitlines()
                for l in lines:
                    img_path = '%s/'%self.root+l[7:]
                    self.val_imgs.append(img_path)
                    
    def __getitem__(self, index):  
        if self.mode=='labeled' or self.mode == 'labeled_svd':
            img_path = self.train_imgs[index]
            target = self.train_labels[img_path] 
            prob = self.probability[index]
            image = Image.open(img_path).convert('RGB')    
            img1 = self.transform(image) 
            img2 = self.transform(image) 
            return img1, img2, target, prob              
        elif self.mode=='unlabeled' or self.mode == 'unlabeled_svd':
            img_path = self.train_imgs[index]
            image = Image.open(img_path).convert('RGB')    
            img1 = self.transform(image) 
            img2 = self.transform(image) 
            return img1, img2  
        elif self.mode=='all':
            img_path = self.train_imgs[index]
            target = self.train_labels[img_path]     
            image = Image.open(img_path).convert('RGB')   
            img = self.transform(image)
            return img, target, img_path        
        elif self.mode=='test':
            img_path = self.test_imgs[index]
            target = self.test_labels[img_path]     
            image = Image.open(img_path).convert('RGB')   
            img = self.transform(image) 
            return img, target
        elif self.mode=='val':
            img_path = self.val_imgs[index]
            target = self.test_labels[img_path]     
            image = Image.open(img_path).convert('RGB')   
            img = self.transform(image) 
            return img, target    
        
    def __len__(self):
        if self.mode=='test':
            return len(self.test_imgs)
        if self.mode=='val':
            return len(self.val_imgs)
        else:
            return len(self.train_imgs)
        
class clothing_dataloader():  
    def __init__(self, root, batch_size, num_batches, num_workers):    
        self.batch_size = batch_size
        self.num_workers = num_workers
        self.num_batches = num_batches
        self.root = root
        
                   
        self.transform_train = transforms.Compose([
                transforms.Resize(256),
                transforms.RandomCrop(224),
                transforms.RandomHorizontalFlip(),
                transforms.ToTensor(),                
                transforms.Normalize((0.6959, 0.6537, 0.6371),(0.3113, 0.3192, 0.3214)),                     
            ]) 
        self.transform_test = transforms.Compose([
                transforms.Resize(256),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize((0.6959, 0.6537, 0.6371),(0.3113, 0.3192, 0.3214)),
            ])
    
    def set_initial_exp(self, teacher_idx=None, _truncate_mode=None):
        self.teacher_idx = _teacher_idx
        self.truncate_mode = _truncate_mode
    
    def run(self,mode,pred=[],prob=[],paths=[], teacher_idx=None, refinement=None, train_imgs=None):        
        if mode=='warmup':
            warmup_dataset = clothing_dataset(self.root,transform=self.transform_train, mode='all',num_samples=self.num_batches*self.batch_size*2)
            warmup_loader = DataLoader(
                dataset=warmup_dataset, 
                batch_size=self.batch_size*2,
                shuffle=True,
                num_workers=self.num_workers)  
            return warmup_loader
        elif mode=='train':
            labeled_dataset = clothing_dataset(self.root,transform=self.transform_train, mode='labeled',pred=pred, probability=prob,paths=paths,teacher_idx=self.teacher_idx,truncate_mode=self.truncate_mode)
            labeled_loader = DataLoader(
                dataset=labeled_dataset, 
                batch_size=self.batch_size,
                shuffle=True,
                num_workers=self.num_workers)           
            unlabeled_dataset = clothing_dataset(self.root,transform=self.transform_train, mode='unlabeled',pred=pred, probability=prob,paths=paths,teacher_idx=self.teacher_idx,truncate_mode=self.truncate_mode)
            unlabeled_loader = DataLoader(
                dataset=unlabeled_dataset, 
                batch_size=int(self.batch_size),
                shuffle=True,
                num_workers=self.num_workers)   
            return labeled_loader,unlabeled_loader
        elif mode=='train_svd':
            labeled_dataset = clothing_dataset(self.root,transform=self.transform_train, mode='labeled_svd',pred=pred, probability=prob,paths=paths, teacher_idx=teacher_idx, refinement=refinement, train_imgs=train_imgs)
            labeled_loader = DataLoader(
                dataset=labeled_dataset, 
                batch_size=self.batch_size,
                shuffle=True,
                num_workers=self.num_workers)           
            unlabeled_dataset = clothing_dataset(self.root,transform=self.transform_train, mode='unlabeled_svd',pred=pred, probability=prob,paths=paths, teacher_idx=teacher_idx, refinement=refinement, train_imgs=train_imgs)
            unlabeled_loader = DataLoader(
                dataset=unlabeled_dataset, 
                batch_size=int(self.batch_size),
                shuffle=True,
                num_workers=self.num_workers)   
            return labeled_loader,unlabeled_loader
        elif mode=='eval_train':
            eval_dataset = clothing_dataset(self.root,transform=self.transform_test, mode='all',num_samples=self.num_batches*self.batch_size)
            eval_loader = DataLoader(
                dataset=eval_dataset, 
                batch_size=self.batch_size,
                shuffle=False,
                num_workers=self.num_workers)          
            return eval_loader        
        elif mode=='test':
            test_dataset = clothing_dataset(self.root,transform=self.transform_test, mode='test')
            test_loader = DataLoader(
                dataset=test_dataset, 
                batch_size=1000,
                shuffle=False,
                num_workers=self.num_workers)             
            return test_loader             
        elif mode=='val':
            val_dataset = clothing_dataset(self.root,transform=self.transform_test, mode='val')
            val_loader = DataLoader(
                dataset=val_dataset, 
                batch_size=1000,
                shuffle=False,
                num_workers=self.num_workers)             
            return val_loader     