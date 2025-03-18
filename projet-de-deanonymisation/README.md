## Structure du Répertoire

```
projet-de-deanonymisation/
├── CacheHeaderExtractor/
│   └── cache_header_extractor.py
├── DatacenterScanner/
│   └── datacenter_scanner.py
├── DiscordGeoGuesserBot/
│   ├── discord_geoguesser.py
│   └── avatar_random.png   # Exemple d'image pour le changement d'avatar
└── README.md
```

## Instructions d’Utilisation

1. **CacheHeaderExtractor**  
   - Placez le fichier `cache_header_extractor.py` dans le dossier `CacheHeaderExtractor`.
   - Exécutez-le via la commande :  
     ```bash
     python3 cache_header_extractor.py
     ```
   - Entrez une URL (par exemple, `https://www.namecheap.com/favicon.ico`) pour voir les en-têtes relatifs au cache.

2. **DatacenterScanner**  
   - Placez le fichier `datacenter_scanner.py` dans le dossier `DatacenterScanner`.
   - Exécutez-le avec :  
     ```bash
     python3 datacenter_scanner.py
     ```
   - Fournissez l'URL à scanner pour voir les résultats par datacenter.

3. **DiscordGeoGuesserBot**  
   - Placez le fichier `discord_geoguesser.py` dans le dossier `DiscordGeoGuesserBot` et assurez-vous d’avoir un fichier `avatar_random.png` (une image d’exemple pour changer l’avatar).
   - Installez la bibliothèque discord.py (si ce n'est déjà fait) :
     ```bash
     pip install discord.py
     ```
   - Configurez la variable d'environnement `DISCORD_BOT_TOKEN` avec votre token de bot Discord.
   - Lancez le bot avec :  
     ```bash
     python3 discord_geoguesser.py
     ```
   - Dans Discord, utilisez la commande `!geoguesser <target_user_id>` pour simuler l’attaque et afficher la localisation estimée.


Exemples de scripts, entièrement commentés et fonctionnels, illustrent comment chacun des modules interagit dans le cadre de la méthode de désanonymisation par exploitation du cache CDN.