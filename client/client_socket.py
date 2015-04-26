#-*- encoding: utf-8 -*-

"""
    TcpSocketClient.py    
    Created by Yabin Ping on 4/26/15.
"""

import socket
import struct


class ClientSocket(object):
    """docstring for ClientSocket"""
    def __init__(self, server_addr = "localhost", port = 8000):
        super(ClientSocket, self).__init__()
        self.header             = 163163163
        self.header_len         = 4
        self.message_len		= 4
        self.socket_client      = None
        self.host_addr          = (server_addr, port)    
        self.recived_package    = ""


    def connect(self):
        print """
            Client Connecting...

            Host IP: %s
            Port: %d,
            
            Press Control-C to exit
            """ % (self.host_addr[0], self.host_addr[1])
        self.socket_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_client.connect(self.host_addr)

    def send_message(self, msg):
        msg = struct.pack("<ii%ss"%len(msg), self.header, len(msg), msg)
        self.socket_client.send(msg)

    def recv_package(self):
        """unpack a package to several messages"""
        self.recived_package += self.socket_client.recv(1024)
        package = self.recived_package
        index, pack_len = 0, len(package)
        while index + self.header_len <= pack_len:
            # 检查是否是一个包得开始
            header = struct.unpack("<i",package[index : index + self.header_len])[0]
            if header != self.header:
                index += self.header_len
                continue
            # 跳过包头
            index += self.header_len
            # 得到包头，计算消息的长度
            message_len = struct.unpack("<i",package[index : index + self.message_len])[0]
            if message_len + self.message_len <= pack_len:
                # 跳过消息包头长度
                index += self.message_len
                message = struct.unpack("<%ss" % message_len, package[index: index + message_len])[0]
                print message
                # 跳过消息长度
                index += message_len 
            else:
                # 回退包头长度
                index -= self.header_len
        # 把剩下未处理完的放回
        self.recived_package = package[index:-1]

if __name__ == '__main__':
    client = ClientSocket()
    client.connect()
    client.send_message("hello world!")
    client.recv_package()