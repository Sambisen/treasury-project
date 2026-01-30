# NIBOR Terminal - Setup Guide

## Snabbstart (3 steg)

### 1. Installera Python
- Ladda ner Python 3.11+ från [python.org](https://www.python.org/downloads/)
- **VIKTIGT:** Kryssa i "Add Python to PATH" vid installation

### 2. Installera dependencies
Öppna PowerShell/CMD i projektmappen och kör:
```
pip install -r requirements.txt
```

### 3. Skapa skrivbordsgenväg
Dubbelklicka på `create_shortcut.bat` i projektmappen - skapar en ikon på skrivbordet.

---

## Krav

### OneDrive-mappstruktur
Appen förväntar sig denna struktur i din OneDrive:
```
OneDrive - Swedbank/
└── GroupTreasury-ShortTermFunding - Documents/
    └── Referensräntor/
        └── Nibor/
            ├── Nibor fixing Q1 2026.xlsx    (Excel-filen)
            ├── Wheights.xlsx                 (Vikter)
            ├── Nibor Days.xlsx               (Dagar)
            ├── Nibor logg/                   (Loggfiler)
            └── Bilder/                       (Logotyper)
```

### Bloomberg Terminal
- Bloomberg Terminal måste vara installerat och köra
- Appen ansluter automatiskt till lokal Bloomberg-session

---

## Starta appen

### Alternativ 1: Skrivbordsikon (rekommenderat)
Dubbelklicka på "NIBOR Terminal" ikonen på skrivbordet.

### Alternativ 2: Manuellt
```
python main.py
```

### Alternativ 3: DEV-läge
```
python main.py --dev
```

---

## Felsökning

### "Python not found"
- Kontrollera att Python är installerat: `python --version`
- Om inte: installera om Python och kryssa i "Add to PATH"

### "Module not found"
Kör igen:
```
pip install -r requirements.txt
```

### Bloomberg-anslutning misslyckas
- Kontrollera att Bloomberg Terminal körs
- Testa: öppna Excel och kolla att `=BDP()` fungerar

### Excel-fil hittas inte
- Kontrollera att OneDrive är synkroniserat
- Kontrollera mappstrukturen ovan
- Filen måste heta exakt `Nibor fixing QX 20XX.xlsx`

---

## Kontakt
Vid problem, kontakta Treasury-teamet.
