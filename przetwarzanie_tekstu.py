import re

# Wczytanie danych z pliku orig.txt
try:
    with open('orig.txt', 'r', encoding='utf-8') as file:
        tekst = file.read()
except Exception as e:
    print(f"Błąd podczas odczytu pliku: {e}")
    exit(1)

# Zamiana nawiasów kwadratowych na klamrowe
tekst_przetworzony = tekst.replace('[', '{').replace(']', '}')

# Podział tekstu na zdania
# Wzorzec do wyszukiwania końca zdania: kropka, wykrzyknik lub znak zapytania, po którym następuje spacja lub koniec linii
wzorzec_zdania = r'[.!?](?:\s|$)'
zdania = re.split(wzorzec_zdania, tekst_przetworzony)

# Usunięcie pustych zdań
zdania = [zdanie.strip() for zdanie in zdania if zdanie.strip()]

# Zapisanie wyników do pliku mixed_templates
try:
    with open('data/mixed_templates.txt', 'a', encoding='utf-8') as output_file:
        for zdanie in zdania:
            output_file.write(zdanie + '\n')
    print("Przetwarzanie zakończone pomyślnie. Dane zapisano do pliku 'mixed_templates'.")
except Exception as e:
    print(f"Błąd podczas zapisywania do pliku: {e}")
