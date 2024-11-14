import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox

from descoberta import Descoberta
from transferencia import Transferencia

class InterfaceGrafica:
    def __init__(self, name: str):
        self.descoberta = Descoberta(name)
        self.transferencia = Transferencia(self.solicitar_envio_arquivo)
        self.root = tk.Tk()
        self.root.title("Arquivos em Rede Local")
        self.create_widgets()

    def create_widgets(self):
        self.tree = ttk.Treeview(self.root, columns=('Nome', 'IP'), show='headings')
        self.tree.heading('Nome', text='Nome')
        self.tree.heading('IP', text='IP')
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.button_frame = tk.Frame(self.root)
        self.button_frame.pack(side=tk.RIGHT, fill=tk.Y)

        self.atualizar_btn = tk.Button(self.button_frame, text="Atualizar", command=self.atualizar_dispositivos)
        self.atualizar_btn.pack(fill=tk.X, pady=2)

        self.update_tree_and_buttons()

    def update_tree_and_buttons(self):
        for widget in self.button_frame.winfo_children():
            if isinstance(widget, tk.Button) and widget != self.atualizar_btn:
                widget.destroy()

        self.tree.delete(*self.tree.get_children())
        for dispositivo in self.descoberta.get_connected_devices():
            self.tree.insert('', tk.END, values=(dispositivo['name'], dispositivo['ip']))
            btn = tk.Button(self.button_frame, text=f"Enviar para {dispositivo['name']}", command=lambda d=dispositivo: self.enviar_para_dispositivo(d))
            btn.pack(fill=tk.X, pady=2)

    def enviar_para_dispositivo(self, dispositivo):
        file_path = filedialog.askopenfilename()
        if file_path:
            print(f"Enviando {file_path} para {dispositivo['name']} ({dispositivo['ip']})")
            response = self.transferencia.send(file_path, dispositivo['ip'])
            messagebox.showinfo("Resposta", response)

    def atualizar_dispositivos(self):
        print("Atualizando dispositivos...")
        self.descoberta.reload()
        self.update_tree_and_buttons()

    def solicitar_envio_arquivo(self, dispositivo, file_name):
        resposta = messagebox.askyesno("Solicitação de Envio", f"{dispositivo['name']} ({dispositivo['ip']}) deseja enviar {file_name} para você. Deseja aceitar?")
        if resposta:
            print(f"Arquivo aceito de {dispositivo['name']} ({dispositivo['ip']})")
        else:
            print(f"Arquivo recusado de {dispositivo['name']} ({dispositivo['ip']})")

    def run(self):
        self.root.mainloop()

# Exemplo de uso
if __name__ == "__main__":
    app = InterfaceGrafica("Test")
    app.run()

