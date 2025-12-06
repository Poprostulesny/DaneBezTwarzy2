# -*- coding: utf-8 -*-
"""
Skrypt do generowania rozbudowanych plików values.txt dla wszystkich tagów.
Generuje różne formaty i wariacje danych.
"""
import random
import os
from datetime import datetime, timedelta


def generate_names(output_file: str, names_source: str = "data/names.txt", max_count: int = 500):
    """Generuje listę imion z pliku źródłowego."""
    names = []
    
    with open(names_source, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split(',')
            if len(parts) >= 1:
                name = parts[0].strip()
                if name:
                    # Normalizuj wielkość liter (pierwsze wielkie, reszta mała)
                    name = name.capitalize()
                    names.append(name)
    
    # Usuń duplikaty i ogranicz
    names = list(dict.fromkeys(names))[:max_count]
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for name in names:
            f.write(name + '\n')
    
    print(f"Wygenerowano {len(names)} imion do {output_file}")
    return names


def generate_surnames(output_file: str, surnames_source: str = "data/surnames.txt", max_count: int = 500):
    """Generuje listę nazwisk z pliku źródłowego."""
    surnames = set()
    
    with open(surnames_source, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split(',')
            if len(parts) >= 2:
                surname = parts[1].strip()
                if surname and len(surname) > 1:
                    # Normalizuj wielkość liter
                    surname = surname.capitalize()
                    surnames.add(surname)
    
    surnames = list(surnames)[:max_count]
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for surname in surnames:
            f.write(surname + '\n')
    
    print(f"Wygenerowano {len(surnames)} nazwisk do {output_file}")
    return surnames


def generate_pesels(output_file: str, count: int = 200):
    """Generuje numery PESEL w różnych formatach."""
    pesels = []
    
    for _ in range(count):
        # Generuj datę urodzenia
        year = random.randint(1950, 2010)
        month = random.randint(1, 12)
        day = random.randint(1, 28)
        
        # Dla osób urodzonych po 2000 dodaj 20 do miesiąca
        if year >= 2000:
            month_code = month + 20
            year_code = year - 2000
        else:
            month_code = month
            year_code = year - 1900
        
        serial = random.randint(0, 9999)
        
        pesel_base = f"{year_code:02d}{month_code:02d}{day:02d}{serial:04d}"
        
        # Oblicz sumę kontrolną
        weights = [1, 3, 7, 9, 1, 3, 7, 9, 1, 3]
        checksum = sum(int(d) * w for d, w in zip(pesel_base, weights)) % 10
        checksum = (10 - checksum) % 10
        
        pesel = pesel_base + str(checksum)
        pesels.append(pesel)
    
    # Dodaj różne formaty
    formatted_pesels = []
    for p in pesels:
        formatted_pesels.append(p)  # bez formatowania
        # Z spacjami
        formatted_pesels.append(f"{p[:2]} {p[2:4]} {p[4:6]} {p[6:]}")
        # Z myślnikami
        formatted_pesels.append(f"{p[:6]}-{p[6:]}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for pesel in formatted_pesels:
            f.write(pesel + '\n')
    
    print(f"Wygenerowano {len(formatted_pesels)} numerów PESEL do {output_file}")


def generate_dates_of_birth(output_file: str, count: int = 200):
    """Generuje daty urodzenia w różnych formatach."""
    dates = []
    
    base_date = datetime(1950, 1, 1)
    end_date = datetime(2010, 12, 31)
    
    for _ in range(count):
        delta = random.randint(0, (end_date - base_date).days)
        date = base_date + timedelta(days=delta)
        
        # Różne formaty
        formats = [
            date.strftime("%d.%m.%Y"),          # 15.03.1990
            date.strftime("%d-%m-%Y"),          # 15-03-1990
            date.strftime("%Y-%m-%d"),          # 1990-03-15
            date.strftime("%d/%m/%Y"),          # 15/03/1990
            date.strftime("%d %B %Y"),          # 15 March 1990
            date.strftime("%d.%m.%y"),          # 15.03.90
            date.strftime("%-d.%-m.%Y"),        # 5.3.1990
        ]
        
        dates.extend(formats)
    
    # Usuń duplikaty
    dates = list(dict.fromkeys(dates))
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for d in dates:
            f.write(d + '\n')
    
    print(f"Wygenerowano {len(dates)} dat urodzenia do {output_file}")


def generate_dates(output_file: str, count: int = 200):
    """Generuje różne daty (nie urodzenia) w różnych formatach."""
    dates = []
    
    base_date = datetime(2015, 1, 1)
    end_date = datetime(2025, 12, 31)
    
    for _ in range(count):
        delta = random.randint(0, (end_date - base_date).days)
        date = base_date + timedelta(days=delta)
        
        # Różne formaty
        formats = [
            date.strftime("%d.%m.%Y"),
            date.strftime("%d.%m.%Y r."),
            date.strftime("%d-%m-%Y"),
            date.strftime("%Y-%m-%d"),
            date.strftime("%d/%m/%Y"),
            date.strftime("%-d.%-m.%Y"),
            date.strftime("%d %B %Y"),
        ]
        
        dates.extend(formats)
    
    dates = list(dict.fromkeys(dates))
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for d in dates:
            f.write(d + '\n')
    
    print(f"Wygenerowano {len(dates)} dat do {output_file}")


def generate_cities(output_file: str, count: int = 300):
    """Generuje listę polskich miast."""
    cities = [
        # Największe miasta
        "Warszawa", "Kraków", "Łódź", "Wrocław", "Poznań", "Gdańsk", "Szczecin",
        "Bydgoszcz", "Lublin", "Białystok", "Katowice", "Gdynia", "Częstochowa",
        "Radom", "Sosnowiec", "Toruń", "Kielce", "Rzeszów", "Gliwice", "Zabrze",
        "Olsztyn", "Bielsko-Biała", "Bytom", "Zielona Góra", "Rybnik", "Ruda Śląska",
        "Opole", "Tychy", "Gorzów Wielkopolski", "Elbląg", "Płock", "Dąbrowa Górnicza",
        "Wałbrzych", "Włocławek", "Tarnów", "Chorzów", "Koszalin", "Kalisz", "Legnica",
        "Grudziądz", "Jaworzno", "Słupsk", "Jastrzębie-Zdrój", "Nowy Sącz", "Jelenia Góra",
        "Siedlce", "Mysłowice", "Piła", "Konin", "Piotrków Trybunalski", "Inowrocław",
        "Lubin", "Ostrów Wielkopolski", "Suwałki", "Stargard", "Gniezno", "Ostrowiec Świętokrzyski",
        "Siemianowice Śląskie", "Głogów", "Pabianice", "Leszno", "Żory", "Zamość",
        "Pruszków", "Łomża", "Ełk", "Tomaszów Mazowiecki", "Chełm", "Mielec",
        "Kędzierzyn-Koźle", "Przemyśl", "Stalowa Wola", "Tczew", "Biała Podlaska",
        "Bełchatów", "Świdnica", "Będzin", "Zgierz", "Piekary Śląskie", "Racibórz",
        "Legionowo", "Oświęcim", "Świętochłowice", "Starachowice", "Wejherowo",
        "Zawiercie", "Puławy", "Skierniewice", "Starogard Gdański", "Radomsko",
        "Skarżysko-Kamienna", "Tarnobrzeg", "Kołobrzeg", "Rumia", "Kutno", "Ciechanów",
        "Nysa", "Otwock", "Sochaczew", "Sanok", "Bolesławiec", "Zduńska Wola",
        "Piaseczno", "Świnoujście", "Krosno", "Kraśnik", "Żyrardów", "Wodzisław Śląski",
        "Dzierżoniów", "Nowa Sól", "Jarosław", "Mińsk Mazowiecki", "Mikołów",
        "Brzeg", "Knurów", "Chojnice", "Olkusz", "Oleśnica", "Lubliniec", "Gorlice",
        "Nowy Targ", "Police", "Zakopane", "Cieszyn", "Świebodzice", "Łuków",
        "Biłgoraj", "Bochnia", "Brodnica", "Żywiec", "Reda", "Mława", "Augustów"
    ]
    
    # Dodaj warianty (np. "w Warszawie", "do Krakowa")
    expanded = []
    for city in cities:
        expanded.append(city)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for city in expanded:
            f.write(city + '\n')
    
    print(f"Wygenerowano {len(expanded)} miast do {output_file}")


def generate_companies(output_file: str, count: int = 200):
    """Generuje nazwy firm."""
    prefixes = ["", "P.H.U.", "P.P.H.U.", "F.H.U.", "PPHU", "PHU", "FHU", ""]
    
    company_names = [
        # Duże firmy polskie
        "PKO Bank Polski", "Orlen", "PZU", "KGHM", "PGNiG", "PGE", "Lotos",
        "Tauron", "Energa", "Enea", "JSW", "LPP", "CCC", "CD Projekt",
        "Allegro", "InPost", "Żabka", "Biedronka", "Lidl Polska", "Kaufland Polska",
        "Jeronimo Martins", "Eurocash", "Dino", "Emperia", "Maxima",
        # Firmy zagraniczne w Polsce
        "Google Poland", "Microsoft Polska", "Amazon Polska", "Meta Polska",
        "Samsung Electronics Polska", "Apple Polska", "IBM Polska", "Oracle Polska",
        "SAP Polska", "Cisco Polska", "Intel Polska", "HP Polska", "Dell Polska",
        "Volkswagen Poznań", "Toyota Motor Poland", "Mercedes-Benz Polska",
        "BMW Polska", "Audi Polska", "Skoda Auto Polska", "Fiat Polska",
        # Banki
        "mBank", "ING Bank Śląski", "Bank Millennium", "Santander Bank Polska",
        "BNP Paribas Bank Polska", "Credit Agricole", "Alior Bank", "Getin Noble Bank",
        "Bank Pekao", "Bank Pocztowy", "BGŻ BNP Paribas", "Citi Handlowy",
        # Telekomy
        "Orange Polska", "T-Mobile Polska", "Play", "Plus", "Polkomtel",
        # Ubezpieczenia
        "Warta", "Ergo Hestia", "Generali", "Allianz", "AXA", "Aviva",
        # Media
        "TVP", "TVN", "Polsat", "Onet", "WP", "Interia", "Gazeta Wyborcza",
        # Inne
        "Poczta Polska", "PKP", "LOT", "Comarch", "Asseco", "Atos", "Capgemini",
        # Małe firmy z różnymi formami
        "Kowalski Sp. z o.o.", "Nowak S.A.", "Trans-Bud", "Auto-Serwis",
        "Elektro-Instal", "Hydro-Tech", "Termo-System", "Metal-Plast",
        "Drewno-Bud", "Agro-Handel", "Food-Service", "Clean-Pro",
    ]
    
    # Dodaj warianty z prefiksami i sufiksami
    expanded = []
    for name in company_names:
        expanded.append(name)
        if not any(x in name for x in ["Sp.", "S.A.", "Ltd", "GmbH"]):
            expanded.append(f"{name} Sp. z o.o.")
            expanded.append(f"{name} S.A.")
    
    # Dodaj losowe nazwy z prefiksami
    generic_names = ["Budex", "Transex", "Metalex", "Chemex", "Agromax", "Techpol",
                     "Polbud", "Eurobud", "Eurotech", "Polimax", "Intermax", "Multitech"]
    
    for name in generic_names:
        for prefix in prefixes:
            if prefix:
                expanded.append(f"{prefix} {name}")
            else:
                expanded.append(name)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for company in expanded:
            f.write(company + '\n')
    
    print(f"Wygenerowano {len(expanded)} firm do {output_file}")


def generate_credit_cards(output_file: str, count: int = 200):
    """Generuje numery kart kredytowych w różnych formatach."""
    cards = []
    
    # Prefiksy dla różnych typów kart
    prefixes = {
        'visa': ['4'],
        'mastercard': ['51', '52', '53', '54', '55'],
        'amex': ['34', '37'],
        'discover': ['6011', '65'],
    }
    
    for _ in range(count):
        card_type = random.choice(list(prefixes.keys()))
        prefix = random.choice(prefixes[card_type])
        
        if card_type == 'amex':
            length = 15
        else:
            length = 16
        
        # Generuj resztę numeru
        remaining = length - len(prefix) - 1
        middle = ''.join([str(random.randint(0, 9)) for _ in range(remaining)])
        
        # Oblicz cyfrę kontrolną (Luhn)
        partial = prefix + middle
        digits = [int(d) for d in partial]
        for i in range(len(digits) - 1, -1, -2):
            digits[i] *= 2
            if digits[i] > 9:
                digits[i] -= 9
        checksum = (10 - sum(digits) % 10) % 10
        
        card_number = partial + str(checksum)
        
        # Różne formaty
        if card_type == 'amex':
            formatted1 = f"{card_number[:4]}-{card_number[4:10]}-{card_number[10:]}"
            formatted2 = f"{card_number[:4]} {card_number[4:10]} {card_number[10:]}"
        else:
            formatted1 = f"{card_number[:4]}-{card_number[4:8]}-{card_number[8:12]}-{card_number[12:]}"
            formatted2 = f"{card_number[:4]} {card_number[4:8]} {card_number[8:12]} {card_number[12:]}"
        
        cards.append(card_number)
        cards.append(formatted1)
        cards.append(formatted2)
    
    # Usuń duplikaty
    cards = list(dict.fromkeys(cards))
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for card in cards:
            f.write(card + '\n')
    
    print(f"Wygenerowano {len(cards)} numerów kart kredytowych do {output_file}")


def generate_document_numbers(output_file: str, count: int = 200):
    """Generuje numery dokumentów (dowody, paszporty, prawa jazdy)."""
    docs = []
    
    # Polskie dowody osobiste (3 litery + 6 cyfr)
    for _ in range(count // 3):
        letters = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=3))
        numbers = ''.join(random.choices('0123456789', k=6))
        doc = letters + numbers
        docs.append(doc)
        docs.append(f"{letters} {numbers}")
        docs.append(f"{letters}-{numbers}")
    
    # Paszporty (2 litery + 7 cyfr)
    for _ in range(count // 3):
        letters = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=2))
        numbers = ''.join(random.choices('0123456789', k=7))
        doc = letters + numbers
        docs.append(doc)
        docs.append(f"{letters} {numbers}")
    
    # Prawa jazdy (różne formaty)
    for _ in range(count // 3):
        # Format: XXXXX/YY/ZZZZ
        part1 = ''.join(random.choices('0123456789', k=5))
        part2 = ''.join(random.choices('0123456789', k=2))
        part3 = ''.join(random.choices('0123456789', k=4))
        docs.append(f"{part1}/{part2}/{part3}")
        
        # Format: seria i numer
        series = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=2))
        number = ''.join(random.choices('0123456789', k=7))
        docs.append(f"{series}{number}")
    
    docs = list(dict.fromkeys(docs))
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for doc in docs:
            f.write(doc + '\n')
    
    print(f"Wygenerowano {len(docs)} numerów dokumentów do {output_file}")


def generate_bank_accounts(output_file: str, count: int = 200):
    """Generuje numery kont bankowych w różnych formatach."""
    accounts = []
    
    # Polskie kody banków (pierwsze 8 cyfr po PL)
    bank_codes = [
        "10901014", "10201055", "11402004", "10501520", "11602202",
        "12401037", "10301508", "10902170", "10501214", "10901071",
        "24900005", "10201127", "16001071", "17240001", "10301073"
    ]
    
    for _ in range(count):
        bank_code = random.choice(bank_codes)
        account_number = ''.join(random.choices('0123456789', k=16))
        checksum = ''.join(random.choices('0123456789', k=2))
        
        full_account = checksum + bank_code + account_number
        
        # Różne formaty
        formats = [
            f"PL{full_account}",
            f"PL {full_account[:2]} {full_account[2:6]} {full_account[6:10]} {full_account[10:14]} {full_account[14:18]} {full_account[18:22]} {full_account[22:]}",
            f"{full_account[:2]} {full_account[2:6]} {full_account[6:10]} {full_account[10:14]} {full_account[14:18]} {full_account[18:22]} {full_account[22:]}",
            full_account,
        ]
        
        accounts.extend(formats)
    
    accounts = list(dict.fromkeys(accounts))
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for acc in accounts:
            f.write(acc + '\n')
    
    print(f"Wygenerowano {len(accounts)} numerów kont bankowych do {output_file}")


def generate_phones(output_file: str, count: int = 200):
    """Generuje numery telefonów w różnych formatach."""
    phones = []
    
    # Polskie prefiksy komórkowe
    mobile_prefixes = ['50', '51', '53', '57', '60', '66', '69', '72', '73', '78', '79', '88']
    
    # Prefiksy stacjonarne (kierunkowe)
    landline_prefixes = ['12', '22', '32', '42', '52', '58', '61', '71', '81', '91']
    
    for _ in range(count):
        if random.random() < 0.7:  # 70% komórkowe
            prefix = random.choice(mobile_prefixes)
            number = ''.join(random.choices('0123456789', k=7))
            base = prefix + number
            
            formats = [
                f"+48 {base[:3]} {base[3:6]} {base[6:]}",
                f"+48{base}",
                f"48 {base[:3]} {base[3:6]} {base[6:]}",
                f"{base[:3]}-{base[3:6]}-{base[6:]}",
                f"{base[:3]} {base[3:6]} {base[6:]}",
                base,
            ]
        else:  # stacjonarne
            prefix = random.choice(landline_prefixes)
            number = ''.join(random.choices('0123456789', k=7))
            base = prefix + number
            
            formats = [
                f"+48 {base[:2]} {base[2:5]} {base[5:7]} {base[7:]}",
                f"({base[:2]}) {base[2:5]}-{base[5:7]}-{base[7:]}",
                f"{base[:2]} {base[2:5]} {base[5:7]} {base[7:]}",
                base,
            ]
        
        phones.extend(formats)
    
    phones = list(dict.fromkeys(phones))
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for phone in phones:
            f.write(phone + '\n')
    
    print(f"Wygenerowano {len(phones)} numerów telefonów do {output_file}")


def generate_emails(output_file: str, count: int = 200):
    """Generuje adresy email."""
    emails = []
    
    domains = [
        "gmail.com", "yahoo.com", "outlook.com", "wp.pl", "onet.pl", "o2.pl",
        "interia.pl", "poczta.fm", "gazeta.pl", "tlen.pl", "op.pl",
        "hotmail.com", "icloud.com", "protonmail.com", "mail.com"
    ]
    
    company_domains = [
        "firma.pl", "company.com", "biznes.pl", "work.pl", "corp.pl",
        "enterprise.com", "office.pl", "pro.pl"
    ]
    
    first_names = ["jan", "anna", "piotr", "maria", "tomasz", "katarzyna", "adam", "ewa",
                   "michal", "agnieszka", "marcin", "joanna", "pawel", "magdalena"]
    
    last_names = ["kowalski", "nowak", "wisniewski", "wojcik", "kowalczyk", "kaminski",
                  "lewandowski", "zielinski", "szymanski", "wozniak"]
    
    for _ in range(count):
        first = random.choice(first_names)
        last = random.choice(last_names)
        domain = random.choice(domains + company_domains)
        
        # Różne formaty
        patterns = [
            f"{first}.{last}@{domain}",
            f"{first}{last}@{domain}",
            f"{first}_{last}@{domain}",
            f"{first[0]}{last}@{domain}",
            f"{first}.{last}{random.randint(1, 99)}@{domain}",
            f"{last}.{first}@{domain}",
            f"{first}{random.randint(1, 999)}@{domain}",
        ]
        
        emails.append(random.choice(patterns))
    
    emails = list(dict.fromkeys(emails))
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for email in emails:
            f.write(email + '\n')
    
    print(f"Wygenerowano {len(emails)} adresów email do {output_file}")


def generate_addresses(output_file: str, count: int = 200):
    """Generuje adresy zamieszkania."""
    addresses = []
    
    streets = [
        "Marszałkowska", "Piłsudskiego", "Mickiewicza", "Słowackiego", "Kościuszki",
        "Warszawska", "Krakowska", "Poznańska", "Gdańska", "Wrocławska",
        "Lipowa", "Polna", "Leśna", "Ogrodowa", "Kwiatowa", "Słoneczna",
        "Długa", "Krótka", "Szeroka", "Wąska", "Główna", "Rynek",
        "Jana Pawła II", "Solidarności", "Wolności", "Niepodległości",
        "3 Maja", "11 Listopada", "1 Maja", "Armii Krajowej",
        "Sportowa", "Szkolna", "Kościelna", "Parkowa", "Kolejowa"
    ]
    
    street_types = ["ul.", "ulica", "al.", "aleja", "pl.", "plac", "os.", "osiedle"]
    
    cities = ["Warszawa", "Kraków", "Wrocław", "Poznań", "Gdańsk", "Łódź",
              "Szczecin", "Lublin", "Katowice", "Białystok", "Gdynia", "Częstochowa"]
    
    for _ in range(count):
        street = random.choice(streets)
        street_type = random.choice(street_types)
        number = random.randint(1, 150)
        apartment = random.randint(1, 100) if random.random() < 0.6 else None
        postal_code = f"{random.randint(0, 99):02d}-{random.randint(0, 999):03d}"
        city = random.choice(cities)
        
        if apartment:
            street_part = f"{street_type} {street} {number}/{apartment}"
        else:
            street_part = f"{street_type} {street} {number}"
        
        # Różne formaty
        formats = [
            f"{street_part}, {postal_code} {city}",
            f"{street_part}, {city}",
            f"{street_part}\n{postal_code} {city}",
            street_part,
            f"{city}, {street_part}",
        ]
        
        addresses.append(random.choice(formats))
    
    addresses = list(dict.fromkeys(addresses))
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for addr in addresses:
            f.write(addr + '\n')
    
    print(f"Wygenerowano {len(addresses)} adresów do {output_file}")


def generate_ages(output_file: str):
    """Generuje wartości wieku."""
    ages = []
    
    # Różne formaty wieku
    for age in range(0, 101):
        ages.append(str(age))
        if age == 1:
            ages.append("1 rok")
        elif age in [2, 3, 4]:
            ages.append(f"{age} lata")
        else:
            ages.append(f"{age} lat")
    
    # Dodaj słowne opisy
    ages.extend(["kilka", "kilkanaście", "kilkadziesiąt", "pięćdziesiąt kilka"])
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for age in ages:
            f.write(age + '\n')
    
    print(f"Wygenerowano {len(ages)} wartości wieku do {output_file}")


def generate_sex(output_file: str):
    """Generuje wartości płci."""
    values = [
        "mężczyzna", "kobieta", "M", "K", "męska", "żeńska",
        "mężczyzną", "kobietą", "płci męskiej", "płci żeńskiej",
        "chłopak", "dziewczyna", "pan", "pani", "facet"
    ]
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for val in values:
            f.write(val + '\n')
    
    print(f"Wygenerowano {len(values)} wartości płci do {output_file}")


def generate_religions(output_file: str):
    """Generuje wartości wyznań."""
    values = [
        "katolik", "katoliczka", "katolicki", "katolickie", "rzymskokatolicki",
        "prawosławny", "prawosławna", "prawosławie",
        "protestant", "protestantka", "ewangelik", "luteranin",
        "muzułmanin", "muzułmanka", "islam", "islamski",
        "żyd", "żydówka", "judaizm", "wyznania mojżeszowego",
        "buddysta", "buddystka", "buddyzm", "buddyjski",
        "ateista", "ateistka", "ateizm", "bezwyznaniowy", "bezwyznaniowa",
        "agnostyk", "agnostyczka", "agnostycyzm",
        "świadek Jehowy", "Świadkowie Jehowy",
        "grekokatolicka", "greckokatolicki",
        "hinduista", "hinduizm",
        "wierzący", "wierząca", "niewierzący", "niewierząca"
    ]
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for val in values:
            f.write(val + '\n')
    
    print(f"Wygenerowano {len(values)} wartości wyznań do {output_file}")


def generate_political_views(output_file: str):
    """Generuje wartości poglądów politycznych."""
    values = [
        "lewicowe", "prawicowe", "centrowe", "liberalne", "konserwatywne",
        "socjalistyczne", "socjaldemokratyczne", "narodowe", "nacjonalistyczne",
        "libertariańskie", "anarchistyczne", "komunistyczne", "marksistowskie",
        "chrześcijańsko-demokratyczne", "ludowe", "agrarne",
        "proeuropejskie", "eurosceptyczne", "patriotyczne",
        "progresywne", "tradycjonalistyczne", "umiarkowane",
        "lewicowy", "prawicowy", "liberalny", "konserwatywny",
        "zieloni", "ekologiczne", "proekologiczne",
        "populistyczne", "antysystemowe"
    ]
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for val in values:
            f.write(val + '\n')
    
    print(f"Wygenerowano {len(values)} wartości poglądów politycznych do {output_file}")


def generate_ethnicities(output_file: str):
    """Generuje wartości pochodzenia etnicznego."""
    values = [
        "polskie", "polskiego", "Polak", "Polka",
        "ukraińskie", "ukraińskiego", "Ukrainiec", "Ukrainka",
        "niemieckie", "niemieckiego", "Niemiec", "Niemka",
        "rosyjskie", "rosyjskiego", "Rosjanin", "Rosjanka",
        "białoruskie", "białoruskiego", "Białorusin", "Białorusinka",
        "żydowskie", "żydowskiego", "Żyd", "Żydówka",
        "romskie", "romskiego", "Rom", "Romka", "cygańskie",
        "wietnamskie", "wietnamskiego", "Wietnamczyk", "Wietnamka",
        "kaszubskie", "kaszubskiego", "Kaszub", "Kaszubka",
        "śląskie", "śląskiego", "Ślązak", "Ślązaczka",
        "litewskie", "litewskiego", "Litwin", "Litwinka",
        "czeskie", "czeskiego", "Czech", "Czeszka",
        "słowackie", "słowackiego", "Słowak", "Słowaczka",
        "tatarskie", "tatarskiego", "Tatar", "Tatarka",
        "ormiańskie", "ormiańskiego", "Ormianin", "Ormianka"
    ]
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for val in values:
            f.write(val + '\n')
    
    print(f"Wygenerowano {len(values)} wartości pochodzenia etnicznego do {output_file}")


def generate_sexual_orientations(output_file: str):
    """Generuje wartości orientacji seksualnej."""
    values = [
        "heteroseksualna", "heteroseksualny", "hetero",
        "homoseksualna", "homoseksualny", "homo", "gej", "lesbijka",
        "biseksualna", "biseksualny", "bi",
        "aseksualna", "aseksualny",
        "panseksualna", "panseksualny",
        "queer", "nieheteronormatywna", "nieheteronormatywny",
        "niezdefiniowana", "niezdefiniowany",
        "heteroseksualność", "homoseksualność", "biseksualność"
    ]
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for val in values:
            f.write(val + '\n')
    
    print(f"Wygenerowano {len(values)} wartości orientacji seksualnej do {output_file}")


def generate_health_conditions(output_file: str):
    """Generuje wartości stanów zdrowotnych."""
    values = [
        # Choroby przewlekłe
        "cukrzyca", "cukrzyca typu 2", "cukrzyca typu 1", "insulinooporność",
        "nadciśnienie", "nadciśnienie tętnicze", "hipotonia",
        "choroba serca", "niewydolność serca", "arytmia", "migotanie przedsionków",
        "astma", "POChP", "przewlekła obturacyjna choroba płuc",
        "alergia", "alergik", "uczulenie", "atopia",
        # Choroby psychiczne
        "depresja", "zaburzenia depresyjne", "stany depresyjne",
        "schizofrenia", "zaburzenia schizofreniczne",
        "zaburzenia lękowe", "nerwica", "lęki", "ataki paniki",
        "ADHD", "zespół nadpobudliwości", "zaburzenia koncentracji",
        "autyzm", "spektrum autyzmu", "zespół Aspergera",
        "zaburzenia odżywiania", "anoreksja", "bulimia",
        "uzależnienie", "alkoholizm", "narkomania",
        # Inne
        "epilepsja", "padaczka",
        "nowotwór", "rak", "białaczka", "guz",
        "HIV", "AIDS", "HIV-pozytywny",
        "stwardnienie rozsiane", "SM",
        "choroba Parkinsona", "Parkinson",
        "choroba Alzheimera", "demencja", "otępienie",
        "reumatyzm", "RZS", "artretyzm",
        "niepełnosprawność", "niepełnosprawny", "inwalida",
        "niedowidzący", "niedosłyszący", "niesłyszący", "głuchy",
        "na wózku inwalidzkim", "poruszający się na wózku"
    ]
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for val in values:
            f.write(val + '\n')
    
    print(f"Wygenerowano {len(values)} wartości stanów zdrowotnych do {output_file}")


def generate_relatives(output_file: str):
    """Generuje wartości relacji rodzinnych."""
    # Te wartości będą uzupełniane przez generator dynamicznie
    values = [
        "mój brat", "moja siostra", "mój ojciec", "moja matka",
        "mój syn", "moja córka", "mój mąż", "moja żona",
        "mój dziadek", "moja babcia", "mój wnuk", "moja wnuczka",
        "mój wujek", "moja ciocia", "mój kuzyn", "moja kuzynka",
        "mój teść", "moja teściowa", "mój zięć", "moja synowa",
        "mój szwagier", "moja szwagierka", "mój brat cioteczny",
        "syn pana Kowalskiego", "córka pani Nowak",
        "brat mojej żony", "siostra mojego męża",
        "ojciec mojego dziecka", "matka moich dzieci"
    ]
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for val in values:
            f.write(val + '\n')
    
    print(f"Wygenerowano {len(values)} wartości relacji rodzinnych do {output_file}")


def generate_job_titles(output_file: str):
    """Generuje nazwy stanowisk."""
    values = [
        # IT
        "programista", "developer", "software engineer", "senior developer",
        "frontend developer", "backend developer", "full-stack developer",
        "DevOps engineer", "administrator systemów", "analityk IT",
        "tester oprogramowania", "QA engineer", "project manager",
        "product owner", "scrum master", "tech lead", "CTO",
        # Biznes
        "dyrektor", "prezes", "wiceprezes", "członek zarządu", "CEO",
        "kierownik", "manager", "menedżer", "koordynator", "specjalista",
        "analityk biznesowy", "konsultant", "doradca",
        # Finanse
        "księgowy", "główny księgowy", "analityk finansowy", "controller",
        "audytor", "biegły rewident", "doradca podatkowy", "broker",
        # Medycyna
        "lekarz", "lekarka", "pielęgniarz", "pielęgniarka",
        "chirurg", "kardiolog", "pediatra", "psychiatra", "dentysta",
        "farmaceuta", "ratownik medyczny", "fizjoterapeuta",
        # Prawo
        "prawnik", "adwokat", "radca prawny", "sędzia", "prokurator",
        "notariusz", "komornik", "aplikant",
        # Edukacja
        "nauczyciel", "profesor", "wykładowca", "lektor", "pedagog",
        "dyrektor szkoły", "wychowawca",
        # Inne
        "inżynier", "architekt", "mechanik", "elektryk", "hydraulik",
        "kierowca", "sprzedawca", "kasjer", "kelner", "kucharz",
        "policjant", "strażak", "żołnierz", "ochroniarz",
        "dziennikarz", "redaktor", "grafik", "fotograf", "aktor"
    ]
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for val in values:
            f.write(val + '\n')
    
    print(f"Wygenerowano {len(values)} wartości stanowisk do {output_file}")


def generate_school_names(output_file: str):
    """Generuje nazwy szkół."""
    types = [
        "Szkoła Podstawowa", "SP", "Gimnazjum", "Liceum Ogólnokształcące", "LO",
        "Technikum", "Zespół Szkół", "ZS", "Zasadnicza Szkoła Zawodowa",
        "Uniwersytet", "Politechnika", "Akademia", "Wyższa Szkoła"
    ]
    
    patrons = [
        "im. Jana Pawła II", "im. Adama Mickiewicza", "im. Marii Curie-Skłodowskiej",
        "im. Stefana Batorego", "im. Tadeusza Kościuszki", "im. Mikołaja Kopernika",
        "im. Fryderyka Chopina", "im. Marii Konopnickiej", "im. Henryka Sienkiewicza",
        "im. Bolesława Prusa", "im. Józefa Piłsudskiego", "im. Stanisława Staszica"
    ]
    
    cities = ["w Warszawie", "w Krakowie", "we Wrocławiu", "w Poznaniu",
              "w Gdańsku", "w Łodzi", "w Katowicach", "w Lublinie"]
    
    values = []
    
    for t in types:
        for i in range(1, 20):
            values.append(f"{t} nr {i}")
        for patron in patrons[:5]:
            values.append(f"{t} {patron}")
        for city in cities[:3]:
            values.append(f"{t} {city}")
    
    # Konkretne uczelnie
    universities = [
        "Uniwersytet Warszawski", "Uniwersytet Jagielloński",
        "Politechnika Warszawska", "Politechnika Wrocławska",
        "Politechnika Gdańska", "Politechnika Poznańska",
        "Akademia Górniczo-Hutnicza", "SGH", "Szkoła Główna Handlowa",
        "SGGW", "Uniwersytet im. Adama Mickiewicza", "UAM"
    ]
    values.extend(universities)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for val in values:
            f.write(val + '\n')
    
    print(f"Wygenerowano {len(values)} nazw szkół do {output_file}")


def generate_usernames(output_file: str, count: int = 200):
    """Generuje nazwy użytkowników."""
    usernames = []
    
    prefixes = ["", "@", "user_", "pl_", ""]
    
    first_names = ["jan", "anna", "piotr", "maria", "tomasz", "kasia", "adam", "ewa",
                   "michal", "aga", "marcin", "joanna", "pawel", "magda", "kuba", "ola"]
    
    last_names = ["kowalski", "nowak", "wisniewski", "wojcik", "kowalczyk", "kaminski"]
    
    suffixes = ["", "123", "pl", "2000", "xxx", "_official", ".pl", "1990"]
    
    for _ in range(count):
        first = random.choice(first_names)
        last = random.choice(last_names)
        prefix = random.choice(prefixes)
        suffix = random.choice(suffixes)
        
        patterns = [
            f"{prefix}{first}{suffix}",
            f"{prefix}{first}{last}{suffix}",
            f"{prefix}{first}_{last}{suffix}",
            f"{prefix}{first}.{last}{suffix}",
            f"{prefix}{first[0]}{last}{suffix}",
            f"{prefix}{last}{random.randint(1, 99)}",
        ]
        
        usernames.append(random.choice(patterns))
    
    usernames = list(dict.fromkeys(usernames))
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for username in usernames:
            f.write(username + '\n')
    
    print(f"Wygenerowano {len(usernames)} nazw użytkowników do {output_file}")


def generate_secrets(output_file: str, count: int = 100):
    """Generuje hasła i klucze API."""
    secrets = []
    
    # Słabe hasła (często używane)
    weak_passwords = [
        "123456", "password", "qwerty", "abc123", "haslo123", "admin",
        "zaq12wsx", "1qaz2wsx", "password1", "haslo", "tajne", "secret"
    ]
    secrets.extend(weak_passwords)
    
    # Losowe hasła
    for _ in range(count):
        length = random.randint(8, 16)
        chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
        password = ''.join(random.choices(chars, k=length))
        secrets.append(password)
    
    # Klucze API
    for _ in range(count // 2):
        # Format: sk-xxx lub api_xxx
        key_type = random.choice(["sk-", "api_", "key_", "token_", ""])
        key = ''.join(random.choices("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=32))
        secrets.append(f"{key_type}{key}")
    
    secrets = list(dict.fromkeys(secrets))
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for secret in secrets:
            f.write(secret + '\n')
    
    print(f"Wygenerowano {len(secrets)} haseł/kluczy do {output_file}")


def main():
    """Generuje wszystkie pliki values.txt."""
    print("="*60)
    print("Generowanie rozszerzonych plików wartości...")
    print("="*60)
    
    # Sprawdź czy istnieje katalog data
    if not os.path.exists("data"):
        print("Błąd: katalog 'data' nie istnieje!")
        return
    
    # Generuj wszystkie pliki
    generate_names("data/name/values.txt", "data/names.txt", max_count=500)
    generate_surnames("data/surname/values.txt", "data/surnames.txt", max_count=500)
    generate_pesels("data/pesel/values.txt", count=200)
    generate_dates_of_birth("data/date-of-birth/values.txt", count=200)
    generate_dates("data/date/values.txt", count=200)
    generate_cities("data/city/values.txt", count=300)
    generate_companies("data/company/values.txt", count=200)
    generate_credit_cards("data/credit-card-number/values.txt", count=200)
    generate_document_numbers("data/document-number/values.txt", count=200)
    generate_bank_accounts("data/bank-account/values.txt", count=200)
    generate_phones("data/phone/values.txt", count=200)
    generate_emails("data/email/values.txt", count=200)
    generate_addresses("data/address/values.txt", count=200)
    generate_ages("data/age/values.txt")
    generate_sex("data/sex/values.txt")
    generate_religions("data/religion/values.txt")
    generate_political_views("data/political-view/values.txt")
    generate_ethnicities("data/ethnicity/values.txt")
    generate_sexual_orientations("data/sexual-orientation/values.txt")
    generate_health_conditions("data/health/values.txt")
    generate_relatives("data/relative/values.txt")
    generate_job_titles("data/job-title/values.txt")
    generate_school_names("data/school-name/values.txt")
    generate_usernames("data/username/values.txt", count=200)
    generate_secrets("data/secret/values.txt", count=100)
    
    print("\n" + "="*60)
    print("✅ Wszystkie pliki wartości zostały wygenerowane!")
    print("="*60)


if __name__ == "__main__":
    main()
