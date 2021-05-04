import sys

from torchvision import datasets, transforms
from base import BaseDataLoader
from data_loader.cifar10 import get_cifar10
from data_loader.cifar100 import get_cifar100
from data_loader.clothing1m import get_clothing1m
from data_loader.svhn import get_svhn
from utils.parse_config import ConfigParser
from PIL import Image

class SVHNDataLoader(BaseDataLoader):
    def __init__(self, data_dir, batch_size, shuffle=True, validation_split=0.0, num_batches=0, 
                 training=True, num_workers=4, pin_memory=True, config=None, teacher_idx=None):
        
        self.batch_size = batch_size
        self.num_workers = num_workers
        self.num_batches = num_batches
        self.training = training
        
        transform_train = transforms.Compose([
            transforms.RandomCrop(32, padding=2),
            transforms.ColorJitter(
            brightness=63.0 / 255.0, saturation=[0.5, 1.5], contrast=[0.2, 1.8]),
            transforms.ToTensor(),
            transforms.Normalize((0.4376821, 0.4437697, 0.47280442), 
                                 (0.19803012, 0.20101562, 0.19703614))
        ])
        
        transform_val = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize((0.4376821, 0.4437697, 0.47280442), 
                                 (0.19803012, 0.20101562, 0.19703614))
        ])
        
        self.data_dir = data_dir
        
        if config == None:
            config = ConfigParser.get_instance()
        cfg_trainer = config['trainer']
        self.train_dataset, self.val_dataset = get_svhn(config['data_loader']['args']['data_dir'], cfg_trainer,
                                                       train=training, transform_train=transform_train, 
                                                       transform_val=transform_val, noise_file=None, teacher_idx=teacher_idx)
        
        super().__init__(self.train_dataset, batch_size, shuffle, validation_split, num_workers,
                         pin_memory, val_dataset=self.val_dataset)
        

class Clothing1MDataLoader(BaseDataLoader):
    def __init__(self, data_dir, batch_size, shuffle=True, validation_split=0.0, num_batches=0, training=True, num_workers=4, pin_memory=True, config=None):

        self.batch_size = batch_size
        self.num_workers = num_workers
        self.num_batches = num_batches
        self.training = training

        self.transform_train = transforms.Compose([
                transforms.Resize(256),
                transforms.RandomCrop(224),
                transforms.RandomHorizontalFlip(),
                transforms.ToTensor(),                
                transforms.Normalize((0.6959, 0.6537, 0.6371),(0.3113, 0.3192, 0.3214)),                     
            ]) 
        self.transform_val = transforms.Compose([
                transforms.Resize(256),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize((0.6959, 0.6537, 0.6371),(0.3113, 0.3192, 0.3214)),
            ])     

        self.data_dir = data_dir
        if config == None:
            config = ConfigParser.get_instance()
        cfg_trainer = config['trainer']
        self.train_dataset, self.val_dataset = get_clothing1m(config['data_loader']['args']['data_dir'], cfg_trainer, num_samples=self.num_batches*self.batch_size, train=training,
                transform_train=self.transform_train, transform_val=self.transform_val)

        super().__init__(self.train_dataset, batch_size, shuffle, validation_split, num_workers, pin_memory,
                         val_dataset = self.val_dataset)

class CIFAR10DataLoader(BaseDataLoader):
    def __init__(self, data_dir, batch_size, shuffle=True, validation_split=0.0, num_batches=0,  training=True, num_workers=4,  pin_memory=True, config=None, teacher_idx=None):
        if config == None:
            config = ConfigParser.get_instance()
        cfg_trainer = config['trainer']
        
        transform_train = transforms.Compose([
            transforms.RandomCrop(32, padding=4),
            transforms.RandomHorizontalFlip(),
            transforms.ToTensor(),
            transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010)),
        ])
        transform_val = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010)),
        ])
        self.data_dir = data_dir

        noise_file='%sCIFAR10_%.1f_Asym_%s.json'%(config['data_loader']['args']['data_dir'],cfg_trainer['percent'],cfg_trainer['asym'])
        
        self.train_dataset, self.val_dataset = get_cifar10(config['data_loader']['args']['data_dir'], cfg_trainer, train=training, transform_train=transform_train, transform_val=transform_val, noise_file = noise_file, teacher_idx = teacher_idx)

        super().__init__(self.train_dataset, batch_size, shuffle, validation_split, num_workers, pin_memory,
                         val_dataset = self.val_dataset)
        
    def run_loader(self, batch_size, shuffle, validation_split, num_workers, pin_memory):
        super().__init__(self.train_dataset, batch_size, shuffle, validation_split, num_workers, pin_memory,
                         val_dataset = self.val_dataset)



class CIFAR100DataLoader(BaseDataLoader):
    def __init__(self, data_dir, batch_size, shuffle=True, validation_split=0.0, num_batches=0,  training=True, num_workers=4,  pin_memory=True, config=None, teacher_idx=None):
        
        if config is None:
            config = ConfigParser.get_instance()
        cfg_trainer = config['trainer']
        
        transform_train = transforms.Compose([
                #transforms.ColorJitter(brightness= 0.4, contrast= 0.4, saturation= 0.4, hue= 0.1),
                transforms.RandomCrop(32, padding=4),
                transforms.RandomHorizontalFlip(),
                transforms.ToTensor(),
                transforms.Normalize((0.5071, 0.4867, 0.4408), (0.2675, 0.2565, 0.2761)),
            ])
        transform_val = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize((0.5071, 0.4867, 0.4408), (0.2675, 0.2565, 0.2761)),
        ])
        self.data_dir = data_dir
#         cfg_trainer = config['trainer']

        noise_file='%sCIFAR100_%.1f_Asym_%s.json'%(config['data_loader']['args']['data_dir'],cfg_trainer['percent'],cfg_trainer['asym'])

        self.train_dataset, self.val_dataset = get_cifar100(config['data_loader']['args']['data_dir'], cfg_trainer, train=training,
                                                           transform_train=transform_train, transform_val=transform_val, noise_file = noise_file, teacher_idx = teacher_idx)

        super().__init__(self.train_dataset, batch_size, shuffle, validation_split, num_workers, pin_memory,
                         val_dataset = self.val_dataset)
    def run_loader(self, batch_size, shuffle, validation_split, num_workers, pin_memory):
        super().__init__(self.train_dataset, batch_size, shuffle, validation_split, num_workers, pin_memory,
                         val_dataset = self.val_dataset)


