# Milyen AI-t használtunk?
- Claude opus 5.5
- Chatgpt 6 Astra

# Mire használtuk az AI-t?
- Feladat értelmezés
- Kódban található hibák keresése
- Kód írás
- Tervezés
- Tesztelés

# Hogyan ellenőriztük?
Leginkább manuálisan elindítottuk és megnéztük, hogy az eredmény megeggyezik a vártaknak. Emellett átnéztük a kódot, amit visszaadtott, és átnézettük a projektet AI agent-tel hibák.

# 5 konkrét eset
- A server.py eredetileg megírt kódja nem volt helyes, ezért azt át irattuk AI-al (Gpt-6)
- Az interpreter.py eredeti kódja hibásan kezelte a fordított programot, így azt átsrukturáltuk AI segítségével (Gpt-6)
- UI template tervezése (opus 5.5)
- A feladat szétbontása csapattagokra (opus 5.5)
- UI - interpreter összekapcsolásának tervezésében is kivitelezésében (Gpt-6, opus 5.5) 
