
# -*- coding: utf-8 -*-
# Copyright 2018 Stanislav Pidhorskyi
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#  http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
# 
from __future__ import print_function
import torch.utils.data
from torch import optim
from torchvision.utils import save_image
from net import *
import torch.nn.functional as F
from torch.autograd import Variable
import numpy as np
import json
import pickle
import time
import random
import os
from utils import loadbdd100k

use_cuda = torch.cuda.is_available()

FloatTensor = torch.FloatTensor
IntTensor = torch.IntTensor
LongTensor = torch.LongTensor
torch.set_default_tensor_type('torch.FloatTensor')

# If zd_merge true, will use zd discriminator that looks at entire batch.
zd_merge = False

if use_cuda:
    device = torch.cuda.current_device()
    torch.set_default_tensor_type('torch.cuda.FloatTensor')
    FloatTensor = torch.cuda.FloatTensor
    IntTensor = torch.cuda.IntTensor
    LongTensor = torch.cuda.LongTensor
    print("Running on ", torch.cuda.get_device_name(device))


def setup(x):
    if use_cuda:
        return x.cuda()
    else:
        return x.cpu()


def numpy2torch(x):
    return setup(torch.from_numpy(x))


def extract_batch(data, it, batch_size):
    x = numpy2torch(data[it * batch_size:(it + 1) * batch_size, :, :]) / 255.0
    #x.sub_(0.5).div_(0.5)
    return Variable(x)
None

def main(folding_id, inliner_classes, total_classes, folds=5, bdd100k=False, cfg = None):
    batch_size = 128
    mnist_train = []
    mnist_valid = []
    architecture = None

    if bdd100k:
        zsize = 32
        inliner_classes = [0]
        outlier_classes = [1]

        if cfg is not None:
            print("Data path: " + str(cfg.img_folder))
            channels = cfg.channels
            image_height = cfg.image_height
            image_width = cfg.image_width
            mnist_train_x, valid_imgs, _ , _ = loadbdd100k.load_bdd100k_data_filename_list(cfg.img_folder, cfg.norm_filenames, cfg.out_filenames, cfg.n_train, cfg.n_val, cfg.n_test, cfg.out_frac, image_height, image_width, channels, shuffle=cfg.shuffle)
            architecture = cfg.architecture
        else:
            print("No configuration provided for BDD100K, using standard configuration")
            channels = 3
            image_height = 192
            image_width = 320
            architecture = "b1"
            # TODO: ADD STANDARD CONFIG (HARD CODED)

        print("Transposing data to 'channels first'")
        mnist_train_x = np.moveaxis(mnist_train_x,-1,1)
        valid_imgs = np.moveaxis(valid_imgs,-1,1)
	
        print("Converting data from uint8 to float32")
        mnist_train_x = np.float32(mnist_train_x)
        valid_imgs = np.float32(valid_imgs)
        
        # Labels for training data
        mnist_train_y = np.zeros((len(mnist_train_x),),dtype=np.int)

        for img in valid_imgs:
            mnist_valid.append((0,img))

    else:
        zsize = 32
        channels = 1
        image_height = 32
        image_width = 32
        for i in range(folds):
            if i != folding_id:
                with open('data_fold_%d.pkl' % i, 'rb') as pkl:
                    fold = pickle.load(pkl, encoding='latin1')
                if len(mnist_valid) == 0:
                    mnist_valid = fold
                else:
                    mnist_train += fold

        outlier_classes = []
        for i in range(total_classes):
            if i not in inliner_classes:
                outlier_classes.append(i)

        #keep only train classes
        mnist_train = [x for x in mnist_train if x[0] in inliner_classes]

        random.shuffle(mnist_train)

        def list_of_pairs_to_numpy(l):
            return np.asarray([x[1] for x in l], np.float32), np.asarray([x[0] for x in l], np.int)

        mnist_train_x, mnist_train_y = list_of_pairs_to_numpy(mnist_train)

    print("Train set size:", len(mnist_train_x))
    print("Data type:", mnist_train_x.dtype)
    print("Max pixel value:", np.amax(mnist_train_x))
    G = Generator(zsize, channels = channels, architecture = architecture)
    setup(G)
    G.weight_init(mean=0, std=0.02)

    D = Discriminator(channels = channels, architecture = architecture)
    setup(D)
    D.weight_init(mean=0, std=0.02)

    E = Encoder(zsize, channels = channels, architecture = architecture)
    setup(E)
    E.weight_init(mean=0, std=0.02)

    if zd_merge:
        ZD = ZDiscriminator_mergebatch(zsize, batch_size).to(device)
    else:
        ZD = ZDiscriminator(zsize, batch_size).to(device)

    setup(ZD)
    ZD.weight_init(mean=0, std=0.02)

    lr = 0.002

    G_optimizer = optim.Adam(G.parameters(), lr=lr, betas=(0.5, 0.999))
    D_optimizer = optim.Adam(D.parameters(), lr=lr, betas=(0.5, 0.999))
    E_optimizer = optim.Adam(E.parameters(), lr=lr, betas=(0.5, 0.999))
    GE_optimizer = optim.Adam(list(E.parameters()) + list(G.parameters()), lr=lr, betas=(0.5, 0.999))
    ZD_optimizer = optim.Adam(ZD.parameters(), lr=lr, betas=(0.5, 0.999))

    train_epoch = 80

    BCE_loss = nn.BCELoss()
    y_real_ = torch.ones(batch_size)
    y_fake_ = torch.zeros(batch_size)

    y_real_z = torch.ones(1 if zd_merge else batch_size)
    y_fake_z = torch.zeros(1 if zd_merge else batch_size)

    sample_size = 64
    sample = torch.randn(sample_size, zsize).view(-1, zsize, 1, 1)

    for epoch in range(train_epoch):
        G.train()
        D.train()
        E.train()
        ZD.train()

        Gtrain_loss = 0
        Dtrain_loss = 0
        Etrain_loss = 0
        GEtrain_loss = 0
        ZDtrain_loss = 0

        epoch_start_time = time.time()

        def shuffle(X):
            np.take(X, np.random.permutation(X.shape[0]), axis=0, out=X)

        shuffle(mnist_train_x)

        if (epoch + 1) % 30 == 0:
            G_optimizer.param_groups[0]['lr'] /= 4
            D_optimizer.param_groups[0]['lr'] /= 4
            GE_optimizer.param_groups[0]['lr'] /= 4
            E_optimizer.param_groups[0]['lr'] /= 4
            ZD_optimizer.param_groups[0]['lr'] /= 4
            print("learning rate change!")

        for it in range(len(mnist_train_x) // batch_size):
            x = extract_batch(mnist_train_x, it, batch_size).view(-1, channels, image_height, image_width)
           # print("Batch type:")
           # print(type(x))
           # print("Shape of batch:")
           # print(x.shape)
            #############################################

            D.zero_grad() 

            D_result = D(x).squeeze() # removes all dimensions with size 1
            D_real_loss = BCE_loss(D_result, y_real_)

            z = torch.randn((batch_size, zsize)).view(-1, zsize, 1, 1)
            z = Variable(z)

            x_fake = G(z).detach()
 #           print("Shape of x_fake:",x_fake.shape)
            D_result = D(x_fake).squeeze()
            D_fake_loss = BCE_loss(D_result, y_fake_)

            D_train_loss = D_real_loss + D_fake_loss
            D_train_loss.backward()

            D_optimizer.step()

            Dtrain_loss += D_train_loss.item()

            #############################################

            G.zero_grad()

            z = torch.randn((batch_size, zsize)).view(-1, zsize, 1, 1)
            z = Variable(z)

            x_fake = G(z)
            D_result = D(x_fake).squeeze()

            G_train_loss = BCE_loss(D_result, y_real_)

            G_train_loss.backward()
            G_optimizer.step()

            Gtrain_loss += G_train_loss.item()

            #############################################

            ZD.zero_grad()

            z = torch.randn((batch_size, zsize)).view(-1, zsize)
            z = Variable(z)

            ZD_result = ZD(z).squeeze()
            ZD_real_loss = BCE_loss(ZD_result, y_real_z)

            z = E(x).squeeze().detach()

            ZD_result = ZD(z).squeeze()
            ZD_fake_loss = BCE_loss(ZD_result, y_fake_z)

            ZD_train_loss = ZD_real_loss + ZD_fake_loss
            ZD_train_loss.backward()

            ZD_optimizer.step()

            ZDtrain_loss += ZD_train_loss.item()

            #############################################

            E.zero_grad()
            G.zero_grad()

            z = E(x)
            x_d = G(z)

            ZD_result = ZD(z.squeeze()).squeeze()

            E_loss = BCE_loss(ZD_result, y_real_z) * 2.0

            Recon_loss = F.binary_cross_entropy(x_d, x)

            (Recon_loss + E_loss).backward()

            GE_optimizer.step()

            GEtrain_loss += Recon_loss.item()
            Etrain_loss += E_loss.item()

            if it == 0:
                directory = 'results'+str(inliner_classes[0])
                if not os.path.exists(directory):
                    os.makedirs(directory)
                comparison = torch.cat([x[:64], x_d[:64]])
                save_image(comparison.cpu(),
                           'results'+str(inliner_classes[0])+'/reconstruction_' + str(epoch) + '.png', nrow=64)

        Gtrain_loss /= (len(mnist_train_x))
        Dtrain_loss /= (len(mnist_train_x))
        ZDtrain_loss /= (len(mnist_train_x))
        GEtrain_loss /= (len(mnist_train_x))
        Etrain_loss /= (len(mnist_train_x))

        epoch_end_time = time.time()
        per_epoch_ptime = epoch_end_time - epoch_start_time

        print('[%d/%d] - ptime: %.2f, Gloss: %.3f, Dloss: %.3f, ZDloss: %.3f, GEloss: %.3f, Eloss: %.3f' % ((epoch + 1), train_epoch, per_epoch_ptime, Gtrain_loss, Dtrain_loss, ZDtrain_loss, GEtrain_loss, Etrain_loss))

        with torch.no_grad():
            resultsample = G(sample).cpu()
            directory = 'results'+str(inliner_classes[0])
            os.makedirs(directory, exist_ok = True)
            save_image(resultsample.view(sample_size, channels, image_height, image_width), 'results'+str(inliner_classes[0])+'/sample_' + str(epoch) + '.png')


    print("Training finish!... save training results")
    torch.save(G.state_dict(), "Gmodel.pkl")
    torch.save(E.state_dict(), "Emodel.pkl")
    torch.save(D.state_dict(), "Dmodel.pkl")
    torch.save(ZD.state_dict(), "ZDmodel.pkl")

if __name__ == '__main__':
    main(0, [0], 10)

