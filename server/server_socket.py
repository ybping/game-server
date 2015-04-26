#-*- coding: utf-8 -*-

"""
    TcpSocketServer.py    
    Created by Yabin Ping on 4/26/15.
"""

import select
import socket
import sys
import struct
import Queue

def RED(str):
    return '\033[1;31;40m' + str + '\033[0m'

def BLUE(str):
    return '\033[1;34;40m' + str + '\033[0m'    


NET_STATE_STOP             = 0                 # state: init value
NET_STATE_CONNECTING       = 1                 # state: connecting
NET_STATE_ESTABLISHED      = 2                 # state: connected


class TcpSocketServer(object):
    """
     TcpSocketServer - Basic TCP Socket
    """
    def __init__(self, host_ip="localhost", port=8000):
        super(TcpSocketServer, self).__init__()
        self.host_ip            = host_ip
        self.port               = port
        self.state              = NET_STATE_STOP
        self.server_socket      = None
        self.buffer_size        = 4096
        self.header             = 163163163
        # 包头长度(4 bytes)
        self.header_len         = 4
        # 消息长度(4 bytes)
        self.message_len        = 4
        # 客户socket列表
        self.client_sockets     = []
        # 保存每个socket上次为处理完的数据
        self.packages           = {}
        # 待发送和已接受的消息队列
        self.send_message_queue = Queue.Queue()
        self.received_message_queue = Queue.Queue()

    def start(self):
        """建立TCP连接"""
        print """
            TcpSocketServer Starting...

            Host IP: %s
            Port: %d,
            
            Press Control-C to exit
            """ % (self.host_ip, self.port)

        self.shutdown()
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try: 
            self.server_socket.bind((self.host_ip, self.port))
            # 最多处理的链接数
            self.server_socket.listen(65535)
            self.server_socket.setblocking(0)
            # 添加服务端socket到可读列表
            self.client_sockets.append(self.server_socket)
            self.state = NET_STATE_ESTABLISHED
        except Exception, e:
            try: 
                self.server_socket.close()
            except Exception, e: 
                print "Sever closed", e
            else:
                print e, ". \nServer Address (%s, %d) bind error!" % (self.host_ip, self.port)
                sys.exit(-1)
    

    def server_forever(self, timeout = 0.5):
        """启动服务器，处理I/O请求, 参数timeout为处理select时的超时设置"""
        self.start()
        while True:
            # 处理网络请求
            self.process(timeout)

    
    def process(self, timeout):
        """子类可以覆盖该process方法， 处理具体的I/O请求"""
        if self.client_sockets:
            #===
            # select -- I/O multiplexing
            # select 告诉内核对那些描述符（可读，可写，或异常条件）进行监测，及等待时间
            # 只要其中的任何一个描述符有事件发生，即可返回
            #===
            readable, writeabe, exceptional = select.select(self.client_sockets, self.client_sockets, self.client_sockets, timeout)

            # ===
            # 处理可读的socket
            # ===
            for socket in readable:
                if socket is self.server_socket:    
                    # 如果是服务器的可读socket， 则准备接受客户端的连接
                    connection, client_addr = socket.accept()
                    print "Connection from ", client_addr
                    connection.setblocking(0)
                    self.client_sockets.append(connection)
                    # 缓冲数据队列
                    self.packages[connection] = ''
                else:                               
                    # 如果不是服务器的可读socket， 则准备接受客户端发送的数据, buffer_size = 4096
                    package = socket.recv(self.buffer_size)
                    if len(package) > 4:
                        print RED("Receive Data:"), "%s \b from %s " % (package, socket.getpeername())
                        self.packages[socket] += package
                        # 解包操作
                        self.unpack_package(socket)
                    else:
                        # 没有可用数据的socket，断开连接
                        self.client_sockets.remove(socket)
                        del self.packages[socket]
                        socket.close()
            
            # ===
            # 处理可写的socket
            # ===
            while not self.send_message_queue.empty():
                package = self.send_message_queue.get_nowait()
                for socket in writeabe:
                    socket.send(package)

            # ===
            # 处理出错的socket
            # ===
            for socket in exceptional:
                self.client_sockets.remove(socket)
                del self.packages[socket]
                socket.close()


    def pack_message(self, message):
        """pack a message to a struct package"""
        fmt = "<ii%ss" % len(message)
        package = struct.pack(fmt, self.header, len(message), message)
        print package
        self.send_message_queue.put_nowait(package)

    def unpack_package(self, socket):
        """unpack a package to several messages"""
        package = self.packages[socket]
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
                self.received_message_queue.put_nowait(message)
                self.pack_message(message)
                # 跳过消息长度
                index += message_len 
            else:
                # 回退包头长度
                index -= self.header_len
        # 把剩下未处理完的放回
        self.packages[socket] = package[index:-1]

    def shutdown(self):
        if self.server_socket:
            try:
                print "TcpSocketServer Shutdown..."
                self.server_socket.close()
            except :
                pass
            self.server_socket = None
            self.state = NET_STATE_STOP



if __name__ == '__main__':
    server = TcpSocketServer()
    server.server_forever()
    












