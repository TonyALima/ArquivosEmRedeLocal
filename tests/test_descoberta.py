from time import sleep
import unittest
import socket
import threading

from arquivos_em_rede_local.descoberta import Descoberta

class TestDescoberta(unittest.TestCase):
    def test_send_discovery(self):
        porta_udp = 9999
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', porta_udp))
        sock.settimeout(2)

        d = Descoberta("Test", porta_udp)
        d.send_discovery()

        # Tenta receber a mensagem de descoberta
        try:
            data, addr = sock.recvfrom(1024)
            self.assertEqual(data.decode(), 'Discovery: Who is out there?')
        except socket.timeout:
            self.fail("Não enviou a mensagem de descoberta")

        sock.close()
    
    def test_listen_discovery(self):
        porta_udp = 9998
        ip = '127.0.0.1'

        d = Descoberta("Test", discovery_port=porta_udp)
        # mock comunication
        d.running_comunication = True

        t = threading.Thread(target=d.listen_discovery, daemon=True)
        t.start()

        # Envia a mensagem de descoberta
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        sock.sendto(b'Discovery: Who is out there?', (ip, porta_udp))
        sleep(.1)
        sock.close()
        
        d.running_comunication = False
        d.running_discovery = False
        t.join()
        self.assertTrue(ip in d.descobertas)

    def create_connected_sockets(port):
        server_sock = socket.create_server(('127.0.0.1', port))

        client_sock = socket.create_connection(('127.0.0.1', port))

        conn, _ = server_sock.accept()
        server_sock.close()
        return conn, client_sock

    def test_send_my_name(self):
        porta_tcp = 9997

        d = Descoberta("Test")
        server_sock, client_sock = TestDescoberta.create_connected_sockets(porta_tcp)
        
        threading.Thread(target=d.send_my_name, args=(server_sock,), daemon=True).start()

        message = ''

        data = client_sock.recv(1024)
        if data:
            message = data.decode()

        server_sock.close()
        client_sock.close()
        self.assertEqual(message, 'My name is Test')

    def test_recive_name(self):
        porta_tcp = 9996

        d = Descoberta("Test")
        server_sock, client_sock = TestDescoberta.create_connected_sockets(porta_tcp)

        result = []
        def f(r):
            r.append(d.recive_name(client_sock)) 

        t1 = threading.Thread(target=f, args=(result,), daemon=True)
        t1.start()

        message = "My name is TestToo"
        server_sock.sendall(message.encode())

        t1.join()
        server_sock.close()
        client_sock.close()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], 'TestToo')

    def test_handle_response(self):
        porta_tcp = 9995
        ip = '127.0.0.1'

        d = Descoberta("Test")
        server_sock, client_sock = TestDescoberta.create_connected_sockets(porta_tcp)
        
        t = threading.Thread(target=d.handle_response, args=(ip, server_sock,),daemon=True)
        t.start()

        recived_message = ''
        data = client_sock.recv(1024)
        if data:
            recived_message = data.decode()

        sleep(.1)
        message = "My name is TestToo"
        client_sock.sendall(message.encode())

        sleep(.1)
        t.join()
        client_sock.close()

        self.assertEqual(recived_message, 'My name is Test')
        self.assertTrue(any(dispositivo['name'] == 'TestToo' for dispositivo in d.get_dispositivos())) 

    def test_listen_response(self):
        porta_tcp = 9994
        ip = '127.0.0.1'

        d = Descoberta("Test", comunication_port=porta_tcp)
        t = threading.Thread(target=d.listen_response, daemon=True)
        t.start()
        client_sock = socket.create_connection((ip, porta_tcp))

        message = b'I am here!'
        client_sock.sendall(message)
        
        recived_message = ''
        data = client_sock.recv(1024)
        if data:
            recived_message = data.decode()

        sleep(.1)
        message = "My name is TestToo"
        client_sock.sendall(message.encode())

        sleep(.1)
        t.join()
        client_sock.close()

        self.assertEqual(recived_message, 'My name is Test')
        self.assertTrue(any(dispositivo['name'] == 'TestToo' for dispositivo in d.get_dispositivos())) 

    def test_start_comunication(self):
        porta_tcp = 9992
        ip = '127.0.0.1'

        d = Descoberta("TestToo", comunication_port=porta_tcp)
        d.descobertas.append(ip)

        server_sock = socket.create_server(('', porta_tcp))
        t = threading.Thread(target=d.start_comunication, daemon=True)
        t.start()
        conn, _ = server_sock.accept()
        server_sock.close()

        recived_message = ''
        data = conn.recv(1024)
        if data:
            recived_message = data.decode()

        sleep(.1)
        message = "My name is Test"
        conn.sendall(message.encode())

        sleep(.1)
        recived_name = ''
        data = conn.recv(1024)
        if data:
            recived_name = data.decode()

        t.join()
        conn.close()

        self.assertEqual(recived_message, 'I am here!')
        self.assertEqual(recived_name, 'My name is TestToo')
        self.assertTrue(any(dispositivo['name'] == 'Test' for dispositivo in d.get_dispositivos())) 

if __name__ == '__main__':
    unittest.main()