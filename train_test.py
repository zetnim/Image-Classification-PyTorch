from os import TMP_MAX
import torch
import torch.nn as nn
import numpy as np
from optimizer import optim 
from pathlib import Path
from plot import trainTestPlot

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

class Training:
    
    def __init__(self, model, optimizer, learning_rate, train_dataloader, num_epochs, 
                test_dataloader, eval=True, plot=True, model_name=None, model_save=False, checkpoint=False):
        self.model = model
        self.learning_rate = learning_rate
        self.optim = optimizer
        self.train_dataloader = train_dataloader
        self.test_dataloader = test_dataloader
        self.num_epochs = num_epochs
        self.eval = eval
        self.plot = plot
        self.model_name = model_name
        self.model_save = model_save
        self.checkpoint = checkpoint

    def runner(self):
        best_accuracy = float('-inf')
        criterion = nn.CrossEntropyLoss()
        if self.model_name in ['alexnet', 'vit', 'mlpmixer', 'resmlp', 'squeezenet', 'senet', 'mobilenetv1', 'resnet', 'gmlp', 'efficientnetv2']:
            self.optimizer, scheduler = optim(model_name=self.model_name, model=self.model, lr=self.learning_rate)

        elif self.optim == 'sgd':
            self.optimizer = torch.optim.SGD(self.model.parameters(), lr=self.learning_rate)
            
        elif self.optim == 'adam':
            self.optimizer = torch.optim.Adam(self.model.parameters(), lr=self.learning_rate)
            
        else:
            pass
        
        train_losses = []
        train_accu = []
        test_losses = []
        test_accu = []
        # Train the model
        total_step = len(self.train_dataloader)
        for epoch in range(self.num_epochs):
            running_loss = 0
            correct = 0
            total = 0
            for i, (images, labels) in enumerate(self.train_dataloader):
                images = images.to(device)
                labels = labels.to(device)
                
                # Forward pass
                outputs = self.model(images)
                loss = criterion(outputs, labels)

                # Backward and optimize
                self.optimizer.zero_grad()
                loss.backward()
                self.optimizer.step()
                running_loss += loss.item()

                _, predicted = outputs.max(1)
                total += labels.size(0)
                correct += predicted.eq(labels).sum().item()
                train_loss=running_loss/len(self.train_dataloader)
                train_accuracy = 100.*correct/total
                if (i+1) % 100 == 0:
                    print ('Epoch [{}/{}], Step [{}/{}], Accuracy: {:.3f}, Train Loss: {:.4f}'
                    .format(epoch+1, self.num_epochs, i+1, total_step, train_accuracy, loss.item()))
                
                
            if self.eval:
                self.model.eval()
                with torch.no_grad():
                    correct = 0
                    total = 0
                    running_loss = 0
                    for images, labels in self.test_dataloader:
                        images = images.to(device)
                        labels = labels.to(device)
                        outputs = self.model(images)
                        loss= criterion(outputs,labels)
                        running_loss+=loss.item()
                        _, predicted = torch.max(outputs.data, 1)
                        total += labels.size(0)
                        correct += (predicted == labels).sum().item()
                        test_loss=running_loss/len(self.test_dataloader)
                        test_accuracy = (correct*100)/total
                    print('Epoch: %.0f | Test Loss: %.3f | Accuracy: %.3f'%(epoch+1, test_loss, test_accuracy))

            if test_accuracy > best_accuracy and self.model_save:
                Path('model_store/').mkdir(parents=True, exist_ok=True)
                #torch.save(self.model, 'model_store/'+self.model_name+'_best-model.pt')
                torch.save(self.model.state_dict(), 'model_store/'+self.model_name+'best-model-parameters.pt')

            for p in self.optimizer.param_groups:
                    print(f"Epoch {epoch+1} Learning Rate: {p['lr']}")

            if self.model_name in ['alexnet', 'vit', 'mlpmixer', 'resmlp', 'squeezenet', 'senet', 'mobilenetv1', 'resnet', 'gmlp', 'efficientnetv2']:
                scheduler.step()

            if self.checkpoint:
                path = 'checkpoints/checkpoint{:04d}.pth.tar'.format(epoch)
                Path('checkpoints/').mkdir(parents=True, exist_ok=True)
                torch.save(
                    {
                        'epoch': self.num_epochs,
                        'model_state_dict': self.model.state_dict(),
                        'optimizer_state_dict': self.optimizer.state_dict(),
                        'loss': loss
                    }, path
                )


            train_accu.append(train_accuracy)
            train_losses.append(train_loss)
            test_losses.append(test_loss)
            test_accu.append(test_accuracy)
    
        trainTestPlot(self.plot, train_accu, test_accu, train_losses, test_losses, self.model_name)
