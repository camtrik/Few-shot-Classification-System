
import torch
import torch.nn as nn
import torchvision
import torch.nn.functional as F
import torch.optim as optim
from torch.autograd import Variable


class Flatten(nn.Module):
    def __init__(self):
        super(Flatten, self).__init__()

    def forward(self, x):
        # 拉成输入向量第一维*通道数？
        return x.view(x.size(0), -1)


def load_protonet_conv(**kwargs):
    """
    Loads the prototypical network model
    Arg:
        x_dim (tuple): dimension of input image
        hid_dim (int): dimension of hidden layers in conv blocks
        z_dim (int): dimension of embedded image
    Returns:
        Model (Class ProtoNet)
    """
    x_dim = kwargs['x_dim']
    hid_dim = kwargs['hid_dim']
    z_dim = kwargs['z_dim']

    def conv_block(in_channels, out_channels):
        return nn.Sequential(
            nn.Conv2d(in_channels, out_channels, 3, padding=1),
            # 对数据进行归一化处理
            nn.BatchNorm2d(out_channels),
            nn.ReLU(),
            nn.MaxPool2d(2)
        )

    encoder = nn.Sequential(
        conv_block(x_dim[0], hid_dim),
        conv_block(hid_dim, hid_dim),
        conv_block(hid_dim, hid_dim),
        conv_block(hid_dim, z_dim),
        Flatten()
    )

    return ProtoNet(encoder)


class ProtoNet(nn.Module):
    def __init__(self, encoder):
        """
        Args:
            encoder : CNN encoding the images in sample
            n_way (int): number of classes in a classification task
            n_support (int): number of labeled examples per class in the support set
            n_query (int): number of labeled examples per class in the query set
        """
        # encoder相当于是embbedding部分的CNN？
        super(ProtoNet, self).__init__()
        self.encoder = encoder.cuda()

    def set_forward_loss(self, sample):
        """
        Computes loss, accuracy and output for classification task
        Args:
            sample (torch.Tensor): shape (n_way, n_support+n_query, (dim))
        Returns:
            torch.Tensor: shape(2), loss, accuracy and y_hat
        """
        sample_images = sample['images'].cuda()
        n_way = sample['n_way']
        n_support = sample['n_support']
        n_query = sample['n_query']
        class_name = sample['class_name']

        # e.g. 取出的shape为[8, 5, 3, 28, 28],即每类五张图作为support set
        x_support = sample_images[:, :n_support]
        x_query = sample_images[:, n_support:]

        # target indices are 0 ... n_way-1
        # 生成一个8*5*1的张量
        target_inds = torch.arange(0, n_way).view(n_way,
                                                  1, 1).expand(n_way, n_query, 1).long()
        print("traget_inds shape", target_inds.shape)
        target_inds = Variable(target_inds, requires_grad=False)
        target_inds = target_inds.cuda()

        # encode images of the support and the query set
        # support set和query set前两维合并（即size[40, 3, 28, 28]）
        # 并把两个集合按照第一维叠加[80, 3, 28, 28]
        x = torch.cat([x_support.contiguous().view(n_way * n_support, *x_support.size()[2:]),
                       x_query.contiguous().view(n_way * n_query, *x_query.size()[2:])], 0)

        # encoder是一系列卷积层，先做embbeding，提取成连续向量
        z = self.encoder.forward(x)
        # 卷积层输出的通道数
        # 输出的是80个长度为64的向量
        print("embbeding shape: ", z.shape)
        z_dim = z.size(-1)  # usually 64
        # 前40（n_way*n_support）个是support set，
        # 将其每类的图片求和（即形成一个原型），获得n_way个长为64的特征向量（即原型）
        z_proto_t = z[:n_way * n_support].view(n_way, n_support, z_dim)
        z_proto = z[:n_way * n_support].view(n_way, n_support, z_dim).mean(1)
        print("proto shape(before mean):", z_proto_t.shape)
        print("proto shape:", z_proto.shape)
        z_query = z[n_way * n_support:]
        print('query shape', z_query.shape)

        # compute distances
        dists = euclidean_dist(z_query, z_proto)
        print('dist shape', dists.shape)
        # compute probabilities
        # -dists:距离越小的说明越可能是那一类，softmax后应该越大
        # view:将40张query再次分割为原来的8类每类5张，
        # [8,5,8]表示现在8类每类5张图片中，每张对应8个原型的可能性
        log_p_y = F.log_softmax(-dists, dim=1).view(n_way, n_query, -1)
        print('logpy shape', log_p_y.shape)
        loss_val_t = -log_p_y.gather(2, target_inds)
        print('logpy after gather ', loss_val_t.shape)
        # 评估损失，应该是选取正确的标签类， but why?
        # target_int 顺序排列，表示正确标签，如第一行的标签应当为0，如果预测的不是为0则错了
        loss_val = -log_p_y.gather(2, target_inds).squeeze().view(-1).mean()
        print('loss_val', loss_val.item())
        # y_hat 预测成了哪一类
        _, y_hat = log_p_y.max(2)
        acc_val = torch.eq(y_hat, target_inds.squeeze()).float().mean()

        return loss_val, {
            'loss': loss_val.item(),
            'acc': acc_val.item(),
            'y_hat': y_hat
        }

def euclidean_dist(x, y):
    """
    Computes euclidean distance btw x and y
    Args:
      x (torch.Tensor): shape (n, d). n usually n_way*n_query
      y (torch.Tensor): shape (m, d). m usually n_way
    Returns:
      torch.Tensor: shape(n, m). For each query, the distances to each centroid
    """
    n = x.size(0) #40
    m = y.size(0) #8
    d = x.size(1) #64
    assert d == y.size(1)
    #在第n维增加一个维度
    #每个query分别与每个原型proto作欧几里得距离
    x = x.unsqueeze(1).expand(n, m, d)
    y = y.unsqueeze(0).expand(n, m, d)

    return torch.pow(x - y, 2).sum(2)

def protoNetDemo():
    return load_protonet_conv(
                x_dim=(3,28,28),
                hid_dim=64,
                z_dim=64,
                )