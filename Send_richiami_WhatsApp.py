import tkinter as tk
from tkinter import filedialog, messagebox
import csv
import pywhatkit
import time
from datetime import datetime

class WhatsAppSenderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Invio WhatsApp Clienti")
        self.root.geometry("400x550")
        self.root.resizable(False, False)

        # Console di output
        self.console = tk.Text(root, height=15, font=("Consolas", 9), bg="#f0f0f0")
        self.console.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        self.console.insert(tk.END, "Stato: Pronto per l'invio\n\n")

        # Sezione date
        frame_date = tk.Frame(root)
        frame_date.pack(pady=10)

        self.label_data_inizio = tk.Label(frame_date, text="Data inizio (DD-MM-YYYY):", font=("Arial", 11))
        self.label_data_inizio.grid(row=0, column=0, padx=5)
        self.entry_data_inizio = tk.Entry(frame_date, font=("Arial", 11))
        self.entry_data_inizio.grid(row=0, column=1, padx=5)

        self.label_data_fine = tk.Label(frame_date, text="Data fine (DD-MM-YYYY):", font=("Arial", 11))
        self.label_data_fine.grid(row=1, column=0, padx=5, pady=5)
        self.entry_data_fine = tk.Entry(frame_date, font=("Arial", 11))
        self.entry_data_fine.grid(row=1, column=1, padx=5, pady=5)

        # Pulsanti
        self.btn_load = tk.Button(root, 
                                  text="Carica lista clienti (CSV)", 
                                  command=self.load_csv,
                                  bg="#1da1f2", 
                                  fg="white", 
                                  font=("Arial", 11))
        self.btn_load.pack(pady=10)

        self.btn_send = tk.Button(root, 
                                  text="Invia messaggi", 
                                  command=self.send_messages,
                                  bg="#28a745", 
                                  fg="white", 
                                  font=("Arial", 11, "bold"))
        self.btn_send.pack(pady=10)

        self.clienti = []

    def load_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("File CSV", "*.csv")])
        if not file_path:
            return

        try:
            with open(file_path, newline='', encoding='latin-1') as csvfile:
                lines = csvfile.readlines()
                csvfile.seek(0)
                
                header_line = None
                for i, line in enumerate(lines):
                    if 'Cognome' in line and 'Targa' in line and ('Cellulare' in line or 'Tel. Proprietario' in line):
                        header_line = i
                        break
                
                if header_line is None:
                    messagebox.showerror("Errore", "Intestazione non trovata nel file CSV!")
                    return
                
                csvfile.seek(0)
                for _ in range(header_line):
                    next(csvfile)
                
                reader = csv.DictReader(csvfile, delimiter=';')
                
                self.clienti = []
                for row in reader:
                    try:
                        cliente = {
                            'cognome': row.get('Cognome', '').strip(),
                            'nome': row.get('Nome', '').strip(),
                            'targa': row.get('Targa', '').strip(),
                            'data': row.get('Data Domanda', '').strip(),
                            'cellulare': row.get('Cellulare', row.get('Tel. Proprietario', '')).strip()
                        }
                        
                        if cliente['cellulare'] and cliente['cellulare'].lower() != 'nessuna':
                            self.clienti.append(cliente)
                            
                    except KeyError as e:
                        print(f"Campo mancante: {e}")
                    except Exception as e:
                        print(f"Errore: {str(e)}")
                
                messagebox.showinfo("CSV caricato", f"{len(self.clienti)} clienti validi caricati!")

        except Exception as e:
            messagebox.showerror("Errore", f"Errore nel caricamento CSV:\n{str(e)}")

    def _pulisci_numero(self, numero):
        numero_pulito = ''.join(filter(str.isdigit, numero))
        if numero_pulito.startswith('39'):
            return '+' + numero_pulito
        elif numero_pulito.startswith('0'):
            return '+39' + numero_pulito[1:]
        return '+39' + numero_pulito

    def send_messages(self):
        if not self.clienti:
            messagebox.showwarning("Attenzione", "Prima carica un file CSV con i clienti.")
            return

        try:
            data_inizio = datetime.strptime(self.entry_data_inizio.get(), "%d-%m-%Y")
            data_fine = datetime.strptime(self.entry_data_fine.get(), "%d-%m-%Y")
        except ValueError:
            messagebox.showerror("Errore", "Formato data non valido. Usa DD-MM-YYYY.")
            return

        mesi_italiani = [
            "**GENNAIO**", "**FEBBRAIO**", "**MARZO**", "**APRILE**", "**MAGGIO**", "**GIUGNO**",
            "**LUGLIO**", "**AGOSTO**", "**SETTEMBRE**", "**OTTOBRE**", "**NOVEMBRE**", "**DICEMBRE**"
        ]

        messaggi_inviati = 0
        self.console.delete(1.0, tk.END)
        self.console.insert(tk.END, "=== INIZIO INVIO MESSAGGI ===\n\n")

        for cliente in self.clienti:
            try:
                numero = self._pulisci_numero(cliente['cellulare'])
                if not numero or len(numero) < 10:
                    self.console.insert(tk.END, f"❌ Numero non valido: {cliente['cellulare']}\n")
                    continue

                data_cliente = datetime.strptime(cliente['data'], "%d/%m/%Y")
                
                if data_inizio <= data_cliente <= data_fine:
                    nome_completo = f"{cliente['cognome']} {cliente['nome']}".strip()
                    mese_nome = mesi_italiani[data_cliente.month - 1]

                    msg = f"""Ciao {nome_completo},

Gentile cliente, lo scopo della presente comunicazione è di informarla che entro la fine del
mese di {mese_nome} la revisione per il veicolo targato {cliente['targa']} è in scadenza! 
ORARIO LUN-VEN 8:00 -18:00 SAB 8:00-13:00

È gradito l'appuntamento per effettuare la revisione entro i termini previsti.

Cordiali saluti,
COR. FAZ SNC DI GIULIANO SAGGIO & C
Via degli Olmetti, 3F - 00060 Formello (RM)
Tel. 0690405118"""

                    pywhatkit.sendwhatmsg_instantly(
                        phone_no=numero,
                        message=msg,
                        wait_time=30,
                        tab_close=True
                    )
                    
                    self.console.insert(tk.END, f"✅ Inviato a: {nome_completo}\n")
                    self.console.insert(tk.END, f"📱 Numero: {numero}\n")
                    self.console.insert(tk.END, f"📅 Data: {data_cliente.strftime('%d/%m/%Y')}\n\n")
                    self.console.see(tk.END)
                    self.root.update_idletasks()
                    
                    messaggi_inviati += 1
                    time.sleep(10)

            except Exception as e:
                self.console.insert(tk.END, f"❌ Errore con {cliente['cognome']}:\n{str(e)}\n\n")

        self.console.insert(tk.END, f"\n=== INVIO COMPLETATO ===")
        messagebox.showinfo("Risultato", 
                            f"Invio completato!\n"
                            f"Clienti totali: {len(self.clienti)}\n"
                            f"Messaggi inviati: {messaggi_inviati}")

if __name__ == "__main__":
    root = tk.Tk()
    app = WhatsAppSenderApp(root)
    root.mainloop()
