import os
import copy
import torch
from torch.nn.utils import clip_grad_norm_
from torch.optim.lr_scheduler import ReduceLROnPlateau

from tqdm import tqdm

from utils.helpers import update_avg
from utils.torch import to_device, to_cpu


class Learner():
    
    def __init__(self, model, optimizer, train_loader, valid_loader, loss_fn, 
                 device, n_epochs, model_name, checkpoint_dir, scheduler=None, 
                 metric_spec={}, monitor_metric=True, minimize_score=True, 
                 logger=None, grad_accum=1, grad_clip=100.0, 
                 batch_step_scheduler=True, eval_at_start=False):
        self.model = model
        self.train_loader = train_loader
        self.valid_loader = valid_loader
        self.optimizer = optimizer
        self.loss_fn = loss_fn
        self.device = device
        self.n_epochs = n_epochs
        self.model_name = model_name
        self.checkpoint_dir = checkpoint_dir
        self.scheduler = scheduler
        self.metric_name = list(metric_spec)[0]
        self.metric_fn = metric_spec[self.metric_name]
        self.monitor_metric = monitor_metric
        self.minimize_score = minimize_score
        self.logger = logger
        self.grad_accum = grad_accum
        self.grad_clip = grad_clip
        self.batch_step_scheduler = batch_step_scheduler
        self.eval_at_start = eval_at_start

        self.best_epoch, self.best_score = -1, 1e6 if minimize_score else -1e6
    
    @property
    def best_checkpoint_file(self): 
        return f'{self.checkpoint_dir}{self.model_name}_best.pth'

    def train(self):
        self.model.to(self.device)

        if self.eval_at_start: self.validate(epoch=-1)

        for epoch in range(self.n_epochs):
            self.info('epoch {}: \t Start training...'.format(epoch))
            self.train_preds, self.train_targets = [], []
            self.model.train()
            train_loss, train_metrics = self.train_epoch()
            self.info(self._get_metric_string(epoch, train_loss, train_metrics))
            
            self.validate(epoch)
            
            if not self.batch_step_scheduler and self.scheduler is not None: 
                self.scheduler.step()
                
        self._on_training_end()

    def validate(self, epoch):
        self.info('epoch {}: \t Start validation...'.format(epoch))
        
        self.valid_preds, self.valid_targets = [], []
        self.model.eval()
        val_score, val_loss, val_metrics = self.valid_epoch()
        self.info(self._get_metric_string(epoch, val_loss, val_metrics, 'valid'))
            
        if ((self.minimize_score and (val_score < self.best_score)) or 
            ((not self.minimize_score) and (val_score > self.best_score))):
            self.best_score, self.best_epoch = val_score, epoch
            self.save_model(self.best_checkpoint_file)
            self.info('best model: epoch {} - {:.5}'.format(epoch, val_score))
        else:
            self.info(f'model not improved for {epoch-self.best_epoch} epochs')
            
    def train_epoch(self):
        tqdm_loader = tqdm(self.train_loader)
        curr_loss_avg = 0

        for batch_idx, (inputs, targets) in enumerate(tqdm_loader):
            inputs, targets = self.to_device(inputs), targets.to(self.device)
            preds, loss = self.train_batch(inputs, targets, batch_idx)
            
            self.train_preds.append(to_cpu(preds))
            self.train_targets.append(to_cpu(targets))

            curr_loss_avg = update_avg(curr_loss_avg, loss, batch_idx)
            
            base_lr = self.optimizer.param_groups[0]['lr']
            tqdm_loader.set_description('loss: {:.4} base_lr: {:.6}'.format(
                round(curr_loss_avg, 4), round(base_lr, 6)))

        metric_score = self.metric_fn(
            torch.cat(self.train_preds), torch.cat(self.train_targets)).item()

        return curr_loss_avg, {self.metric_name: metric_score}
    
    def valid_epoch(self):
        tqdm_loader = tqdm(self.valid_loader)
        curr_loss_avg = 0
        
        with torch.no_grad():
            for batch_idx, (inputs, targets) in enumerate(tqdm_loader):
                with torch.no_grad():
                    inputs, targets = self.to_device(inputs), targets.to(self.device)
                    preds, loss = self.valid_batch(inputs, targets)

                    self.valid_preds.append(to_cpu(preds))
                    self.valid_targets.append(to_cpu(targets))

                    curr_loss_avg = update_avg(curr_loss_avg, loss, batch_idx)
                    
                    tqdm_loader.set_description('loss: {:.4}'.format(round(curr_loss_avg, 4)))

        metric_score = self.metric_fn(
            torch.cat(self.valid_preds), torch.cat(self.valid_targets)).item()
        if self.monitor_metric: score = metric_score
        else: score = curr_loss_avg

        return score, curr_loss_avg, {self.metric_name: metric_score}
    
    def train_batch(self, batch_inputs, batch_targets, batch_idx):
        preds, loss = self.get_loss_batch(batch_inputs, batch_targets)

        loss.backward()

        if batch_idx % self.grad_accum == self.grad_accum - 1:
            clip_grad_norm_(self.model.parameters(), self.grad_clip)
            self.optimizer.step()
            self.optimizer.zero_grad()

        if self.batch_step_scheduler and self.scheduler is not None: 
            self.scheduler.step()
        return preds, loss.item()
    
    def valid_batch(self, batch_inputs, batch_targets):
        preds, loss = self.get_loss_batch(batch_inputs, batch_targets)
        return preds, loss.item()
    
    def get_loss_batch(self, batch_inputs, batch_targets):
        preds = self.model(*batch_inputs)
        loss = self.loss_fn(preds, batch_targets)
        return preds, loss

    def to_device(self, xs):
        return to_device(xs, self.device)
    
    def load_best_model(self):
        checkpoint = torch.load(self.best_checkpoint_file)
        self.model.load_state_dict(checkpoint['model_state_dict'])

    def save_model(self, checkpoint_file):
        torch.save({'model_state_dict': self.model.state_dict()}, checkpoint_file)

    def info(self, s):
        if self.logger is not None: self.logger.info(s)
        else: print(s)

    def _get_metric_string(self, epoch, loss, metrics, stage='train'):
        base_str = 'epoch {}/{} \t {} : loss {:.5}'.format(
            epoch, self.n_epochs, stage, loss)
        metrics_str = ''.join(' - {} {:.5}'.format(k, v) for k, v in metrics.items())
        return base_str + metrics_str
            
    def _on_training_end(self):
        self.info('TRAINING END: Best score achieved on epoch '
                  f'{self.best_epoch} - {self.best_score:.5f}')
