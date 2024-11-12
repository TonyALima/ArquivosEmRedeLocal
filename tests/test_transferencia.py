import unittest
from unittest.mock import patch, mock_open, MagicMock
from arquivos_em_rede_local.transferencia import Transferencia

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

if __name__ == '__main__':
    unittest.main()
