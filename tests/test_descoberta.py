from time import sleep
import unittest
import socket
import threading

from arquivos_em_rede_local.descoberta import Descoberta

class TestDescoberta(unittest.TestCase):
    def test_broadcast_discovery_message(self):
        """
        Testa o envio de uma mensagem de descoberta via UDP.
        """
        porta_udp = 9999
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', porta_udp))
        sock.settimeout(2)

        d = Descoberta("Test", porta_udp)
        d.broadcast_discovery_message()

        # Tenta receber a mensagem de descoberta
        try:
            data, _ = sock.recvfrom(1024)
            self.assertEqual(data.decode(), 'Discovery: Who is out there?')
        except socket.timeout:
            self.fail("Não enviou a mensagem de descoberta")

        sock.close()
    
    def test_listen_for_discovery_messages(self):
        """
        Testa a escuta de mensagens de descoberta via UDP.
        """
        porta_udp = 9998
        ip = '127.0.0.1'

        d = Descoberta("Test", discovery_port=porta_udp)
        # mock comunication
        d.running_comunication = True

        t = threading.Thread(target=d.listen_for_discovery_messages, daemon=True)
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
        """
        Cria um par de sockets conectados para comunicação TCP.
        """
        server_sock = socket.create_server(('127.0.0.1', port))

        client_sock = socket.create_connection(('127.0.0.1', port))

        conn, _ = server_sock.accept()
        server_sock.close()
        return conn, client_sock

    def test_send_device_name(self):
        """
        Testa o envio do nome via TCP.
        """
        porta_tcp = 9997

        d = Descoberta("Test")
        server_sock, client_sock = TestDescoberta.create_connected_sockets(porta_tcp)
        
        threading.Thread(target=d.send_device_name, args=(server_sock,), daemon=True).start()

        message = ''

        data = client_sock.recv(1024)
        if data:
            message = data.decode()

        server_sock.close()
        client_sock.close()
        self.assertEqual(message, 'My name is Test')

    def test_receive_device_name(self):
        """
        Testa o recebimento do nome via TCP.
        """
        porta_tcp = 9996

        d = Descoberta("Test")
        server_sock, client_sock = TestDescoberta.create_connected_sockets(porta_tcp)

        result = []
        def f(r):
            r.append(d.receive_device_name(client_sock)) 

        t1 = threading.Thread(target=f, args=(result,), daemon=True)
        t1.start()

        message = "My name is TestToo"
        server_sock.sendall(message.encode())

        t1.join()
        server_sock.close()
        client_sock.close()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], 'TestToo')

    def test_handle_discovery_response(self):
        """
        Testa o manuseio de respostas via TCP.
        """
        porta_tcp = 9995
        ip = '127.0.0.1'

        d = Descoberta("Test")
        server_sock, client_sock = TestDescoberta.create_connected_sockets(porta_tcp)
        
        t = threading.Thread(target=d.handle_discovery_response, args=(ip, server_sock,),daemon=True)
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
        self.assertTrue(any(dispositivo['name'] == 'TestToo' for dispositivo in d.get_connected_devices())) 

    def test_listen_for_responses(self):
        """
        Testa a escuta de respostas via TCP.
        """
        porta_tcp = 9994
        ip = '127.0.0.1'

        d = Descoberta("Test", comunication_port=porta_tcp)
        t = threading.Thread(target=d.listen_for_responses, daemon=True)
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
        self.assertTrue(any(dispositivo['name'] == 'TestToo' for dispositivo in d.get_connected_devices())) 

    def test_initiate_communication(self):
        """
        Testa o início da comunicação via TCP.
        """
        porta_tcp = 9993
        ip = '127.0.0.1'

        d = Descoberta("TestToo", comunication_port=porta_tcp)
        d.descobertas.append(ip)

        server_sock = socket.create_server(('', porta_tcp))
        t = threading.Thread(target=d.initiate_communication, daemon=True)
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
        self.assertTrue(any(dispositivo['name'] == 'Test' for dispositivo in d.get_connected_devices())) 

    def test_connect_two_instances(self):
        """
        Testa a conexão entre duas instâncias.
        """
        porta_udp = 9992
        porta_tcp = 9991
        
        d1 = Descoberta("Test", discovery_port=porta_udp, comunication_port=porta_tcp)
        d2 = Descoberta("TestToo", discovery_port=porta_udp, comunication_port=porta_tcp)

        d1.discovery_listener_thread.start()
        sleep(.1)
        d2.broadcast_discovery_message()
        d2.listen_for_responses()

        self.assertTrue(any(dispositivo['name'] == 'Test' for dispositivo in d2.get_connected_devices()))
        self.assertTrue(any(dispositivo['name'] == 'TestToo' for dispositivo in d1.get_connected_devices()))

if __name__ == '__main__':
    unittest.main()