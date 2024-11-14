import unittest
from unittest.mock import patch, mock_open, MagicMock
from arquivos_em_rede_local.transferencia import Transferencia
import socket
import threading
from time import sleep
import os

class TestTransferencia(unittest.TestCase):
    @patch('arquivos_em_rede_local.transferencia.open', new_callable=mock_open, read_data=b'test data')
    @patch('arquivos_em_rede_local.transferencia.socket.create_connection')
    def test_send_success(self, mock_create_connection, mock_file):
        mock_sock = MagicMock()
        mock_create_connection.return_value.__enter__.return_value = mock_sock
        mock_sock.recv.return_value = b'OK'

        transferencia = Transferencia()
        result = transferencia.send('/path/to/file', '192.168.1.2')

        self.assertEqual(result, "File sent successfully")
        mock_file.assert_called_with('/path/to/file', 'rb')
        mock_sock.sendall.assert_any_call(b'test data')
        mock_sock.sendall.assert_any_call(b'End of file')

    @patch('arquivos_em_rede_local.transferencia.open', new_callable=mock_open)
    @patch('arquivos_em_rede_local.transferencia.socket.create_connection')
    def test_send_failure(self, mock_create_connection, mock_file):
        mock_file.side_effect = Exception("File not found")

        transferencia = Transferencia()
        result = transferencia.send('/path/to/nonexistent/file', '192.168.1.2')

        self.assertEqual(result, "Failed to get file: File not found")

    def test_listen_to_incoming_requests(self):
        """
        Testa a escuta de requisições de envio de arquivos.
        """
        transfer_port = 23010
        file_name = 'test_file.txt'
        file_content = b'This is a test file.'

        # Create a dummy file to send
        with open(file_name, 'wb') as f:
            f.write(file_content)

        t = Transferencia(transfer_port=transfer_port)
        sleep(1)  # Give some time for the listener to start

        def send_file_request():
            with socket.create_connection(('127.0.0.1', transfer_port)) as sock:
                sock.sendall(f'SEND {file_name}'.encode())
                response = sock.recv(1024).decode()
                if response == 'OK':
                    with open(file_name, 'rb') as f:
                        sock.sendall(f.read())
                    sock.sendall(b'End of file')

        threading.Thread(target=send_file_request, daemon=True).start()
        sleep(2)  # Give some time for the file to be transferred

        # Check if the file was received
        with open(file_name, 'rb') as f:
            received_content = f.read()

        self.assertEqual(received_content, file_content)

        # Clean up
        t.running_listener = False
        if t.listen_to_incoming_requests_thread.is_alive():
            t.listen_to_incoming_requests_thread.join()
        os.remove(file_name)

if __name__ == '__main__':
    unittest.main()
