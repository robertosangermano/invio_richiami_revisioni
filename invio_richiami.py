import smtplib
from email.mime.text import MIMEText
from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.pickers import MDDatePicker
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.filemanager import MDFileManager
import pandas as pd
import os
from datetime import datetime


class EmailReminderApp(MDApp):
    def build(self):
        self.selected_file = None
        self.start_date = None
        self.end_date = None

        self.layout = MDBoxLayout(orientation='vertical', padding=10, spacing=10)

        # File chooser
        self.file_label = MDLabel(text="Nessun file selezionato", halign="center")
        self.layout.add_widget(self.file_label)

        self.file_chooser_button = MDRaisedButton(text="Scegli File CSV", on_release=self.select_file)
        self.layout.add_widget(self.file_chooser_button)

        # Date range selectors
        self.start_date_button = MDRaisedButton(text="Seleziona Data Inizio", on_release=self.open_start_date_picker)
        self.layout.add_widget(self.start_date_button)

        self.end_date_button = MDRaisedButton(text="Seleziona Data Fine", on_release=self.open_end_date_picker)
        self.layout.add_widget(self.end_date_button)

        self.date_label = MDLabel(text="Intervallo date: Non selezionato", halign="center")
        self.layout.add_widget(self.date_label)

        # Email configuration
        self.sender_email_label = MDLabel(text="Inserisci la tua email (mittente):", halign="center")
        self.layout.add_widget(self.sender_email_label)

        self.sender_email_input = MDTextField(hint_text="Es. tuoemail@register.it")
        self.layout.add_widget(self.sender_email_input)

        self.sender_password_label = MDLabel(text="Inserisci la tua password:", halign="center")
        self.layout.add_widget(self.sender_password_label)

        self.sender_password_input = MDTextField(hint_text="Password", password=True)
        self.layout.add_widget(self.sender_password_input)

        # Send button
        self.send_button = MDRaisedButton(text="Invia Email di Promemoria")
        self.send_button.bind(on_press=self.send_emails)
        self.layout.add_widget(self.send_button)

        # File Manager Setup
        self.file_manager = MDFileManager(
            exit_manager=self.close_file_manager,
            select_path=self.set_file_path,
        )

        return self.layout

    def select_file(self, instance):
        if os.name == "nt":  # Windows
            start_path = "C:\\"
        else:
            start_path = "/"
        self.file_manager.show(start_path)

    def set_file_path(self, path):
        self.selected_file = path
        self.file_label.text = f"File selezionato: {os.path.basename(path)}"
        self.close_file_manager()

    def close_file_manager(self, *args):
        self.file_manager.close()

    def open_start_date_picker(self, instance):
        date_picker = MDDatePicker()
        date_picker.bind(on_save=self.set_start_date)
        date_picker.open()

    def set_start_date(self, instance, value, date_range):
        self.start_date = value
        self.update_date_label()

    def open_end_date_picker(self, instance):
        date_picker = MDDatePicker()
        date_picker.bind(on_save=self.set_end_date)
        date_picker.open()

    def set_end_date(self, instance, value, date_range):
        self.end_date = value
        self.update_date_label()

    def update_date_label(self):
        if self.start_date and self.end_date:
            self.date_label.text = f"Intervallo date: {self.start_date} - {self.end_date}"

    def send_emails(self, instance):
        if not self.selected_file:
            self.file_label.text = "Seleziona un file CSV prima di inviare le email!"
            return

        if not self.start_date or not self.end_date:
            self.file_label.text = "Seleziona un intervallo di date valido!"
            return

        try:
            data = pd.read_csv(self.selected_file, delimiter=";")
            data.columns = data.columns.str.strip()
            if "Unnamed: 2" in data.columns:
                data = data.drop(columns=["Unnamed: 2"], errors='ignore')
            print(f"Colonne trovate nel file CSV: {data.columns.tolist()}")
        except Exception as e:
            self.file_label.text = f"Errore nella lettura del file CSV: {e}"
            return

        if "Email" not in data.columns or "Data" not in data.columns or "Targa" not in data.columns:
            self.file_label.text = 'Il file CSV deve contenere colonne "Data", "Email" e "Targa".'
            return

        try:
            data["Data"] = pd.to_datetime(data["Data"], errors='coerce')
            filtered_data = data[(data["Data"] >= pd.Timestamp(self.start_date)) & 
                                 (data["Data"] <= pd.Timestamp(self.end_date))]
        except Exception as e:
            self.file_label.text = f"Errore nel filtraggio delle date: {e}"
            return

        if filtered_data.empty:
            self.file_label.text = "Nessuna email trovata per l'intervallo di date selezionato."
            return

        sender_email = self.sender_email_input.text
        sender_password = self.sender_password_input.text

        try:
            # Configura il server SMTP di Register.it
            server = smtplib.SMTP("authsmtp.register.it", 587)
            server.starttls()
            server.login(sender_email, sender_password)
        except Exception as e:
            self.file_label.text = f"Errore nella connessione al server email: {e}"
            return

        try:
            for _, row in filtered_data.iterrows():
                email = row["Email"]
                targa = row["Targa"]
                msg = MIMEText(f"Gentile cliente ci teniamo a informarla che la revisione della sua auto targata {targa} è in scadenza in questo mese.Distinti  saluti  Centro Revisioni Cor.faz.")
                msg["Subject"] = "Promemoria Scadenza Revisione"
                msg["From"] = sender_email
                msg["To"] = email
                server.sendmail(sender_email, email, msg.as_string())
                print(f"Email inviata con successo a: {email} con targa: {targa}")

            self.file_label.text = "Email inviate con successo! \U0001F389"
        except Exception as e:
            self.file_label.text = f"Errore durante l'invio delle email: {e}"
        finally:
            server.quit()


if __name__ == "__main__":
    EmailReminderApp().run()
