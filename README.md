# Projet de Désanonymisation via Exploitation du Caching CDN
**Version : 1.2.0**  
**Date : 2025-03-18**

---

## Table des Matières

1. [Introduction et Contexte](#introduction-et-contexte)  
2. [Architecture Technique](#architecture-technique)  
   2.1. [Fonctionnement du Caching chez Cloudflare](#fonctionnement-du-caching-chez-cloudflare)  
   2.2. [Le Rôle du Système Anycast](#le-role-du-systeme-anycast)  
3. [Exploitation du Caching pour la Désanonymisation](#exploitation-du-caching-pour-la-désanonymisation)  
   3.1. [Analyse des En-têtes HTTP](#analyse-des-en-tetes-http)  
   3.2. [Cloudflare Teleport : Traversée des Datacenters](#cloudflare-teleport---traversee-des-datacenters)  
4. [Cas d’Utilisation et Scénarios d’Attaque](#cas-dutilisation-et-scenarios-dattaque)  
   4.1. [Scénario sur Namecheap](#scenario-sur-namecheap)  
   4.2. [Application Réelle : Signal](#application-reelle-signal)  
      4.2.1. [Attaque 1-Clic](#attaque-1-clic-sur-signal)  
      4.2.2. [Attaque 0-Clic via Notifications Push](#attaque-0-clic-sur-signal)  
   4.3. [Application Réelle : Discord](#application-reelle-discord)  
      4.3.1. [Attaque sur Avatars et Emojis](#attaque-sur-avatars-et-emojis)  
      4.3.2. [GeoGuesser – Automatisation via Bot Discord](#geoguesser---automatisation-via-bot-discord)  
5. [Exemples de Code et Automatisation](#exemples-de-code-et-automatisation)  
   5.1. [Extraction d'En-têtes HTTP avec Python](#extraction-dentetes-http-avec-python)  
   5.2. [Script de Scan des Datacenters](#script-de-scan-des-datacenters)  
   5.3. [Pseudo-code du Bot Discord GeoGuesser](#pseudo-code-du-bot-discord-geoguesser)  
6. [Médias et Illustrations](#medias-et-illustrations)  
   6.1. [Images Issues du Raw de Base](#images-issues-du-raw-de-base)  
   6.2. [Vidéos et GIFs](#videos-et-gifs)  
7. [Mesures de Protection et Recommandations](#mesures-de-protection-et-recommandations)  
8. [Bug Bounty et Réponses des Parties Impactées](#bug-bounty-et-reponses-des-parties-impactees)  
9. [Conclusion](#conclusion)  
10. [Licence](#licence)

---

## 1. Introduction et Contexte

Ce projet documente une approche innovante de désanonymisation (aussi appelée « deanonymization ») exploitant la proximité géographique des datacenters CDN de Cloudflare. En observant les en-têtes HTTP renvoyés lors du caching, il est possible d’estimer la position d’un utilisateur avec une précision de l’ordre de 250 miles.

La recherche a mis en évidence que des applications sensibles telles que Signal, Discord, Twitter/X, et d’autres, pouvaient être vulnérables à ce type d’attaque. Les méthodes décrites reposent sur :
- L’exploitation des informations contenues dans les en-têtes HTTP (ex. `cf-cache-status` et `cf-ray`).
- L’utilisation de techniques de redirection via Cloudflare Teleport ou des VPN pour forcer l’acheminement vers des datacenters spécifiques.
- L’automatisation via des scripts et des bots pour réaliser des attaques « 0-clic ».

Ce document se veut à la fois un guide technique et une documentation complète à destination de chercheurs en sécurité, développeurs et administrateurs systèmes.

---

## 2. Architecture Technique

### 2.1 Fonctionnement du Caching chez Cloudflare

Cloudflare est l’un des CDN les plus populaires, possédant des centaines de datacenters répartis dans plus de 330 villes à travers le monde. Le caching améliore la performance des sites en stockant des copies de contenus fréquemment demandés.

- **Stockage en cache** :  
  Lorsqu’un utilisateur demande une ressource (image, vidéo, page web), Cloudflare vérifie si la ressource est disponible dans le cache du datacenter local. Si oui, la ressource est servie rapidement (indiqué par l’en-tête `cf-cache-status: HIT`), sinon, la ressource est récupérée du serveur d’origine puis mise en cache.

- **En-têtes HTTP** :  
  Les réponses HTTP incluent notamment :
  - `cf-cache-status` : Indique l’état du cache (HIT ou MISS).
  - `cf-ray` : Contient un identifiant qui inclut le code de l’aéroport le plus proche du datacenter ayant servi la requête.

Exemple d’en-tête :
> `cf-cache-status: HIT`  
> `cf-ray: 66a1e3a1c9e5f0a3-AMS`

> **Image illustrative :**  
> ![Exemple d'en-tête Cloudflare](https://gist.github.com/user-attachments/assets/95e1a39a-ed25-4531-9c57-a1b43c616519)

### 2.2 Le Rôle du Système Anycast

Le système anycast permet aux requêtes d’être automatiquement dirigées vers le datacenter le plus proche géographiquement de l’utilisateur. Cette fonctionnalité, bien que bénéfique pour la performance, offre une fenêtre d’exploitation :
- **Limitation géographique** :  
  Les connexions TCP s’acheminent vers le datacenter le plus proche, rendant possible l’inférence de la localisation de l’utilisateur.
- **Contournement** :  
  En modifiant l’origine de la requête (via Cloudflare Workers ou VPN), il est possible de forcer le passage par un datacenter précis.

---

## 3. Exploitation du Caching pour la Désanonymisation

### 3.1 Analyse des En-têtes HTTP

L’attaque repose sur l’observation des en-têtes HTTP envoyés par Cloudflare. Pour une ressource donnée, l’analyse des en-têtes permet de déterminer :
- Si la ressource est servie depuis le cache (`HIT`).
- Le datacenter ayant servi la requête, via le code contenu dans `cf-ray`.

**Schéma de fonctionnement :**
1. Forcer le chargement d’une ressource (ex. favicon) sur un site supporté par Cloudflare.
2. Récupérer les en-têtes HTTP et extraire `cf-cache-status` et `cf-ray`.
3. Identifier le datacenter et, par extension, la localisation approximative de l’utilisateur.

> **Exemple d’utilisation :**  
> Une requête sur `https://www.namecheap.com/favicon.ico` permet d’observer dans le cache que plusieurs datacenters (par exemple, de Tokyo, Newark, etc.) ont servi la ressource récemment.

### 3.2 Cloudflare Teleport – Traversée des Datacenters

Cloudflare Teleport est un outil (initialement développé via Cloudflare Workers) permettant d’envoyer des requêtes HTTP vers des datacenters spécifiques en exploitant une plage d’IP interne de Cloudflare (utilisée par Cloudflare WARP).

- **Principe** :  
  En redirigeant les requêtes à l’aide d’une URL paramétrée, il est possible de cibler un datacenter particulier.  
  Exemple :
  ```
  https://cfteleport.xyz/?proxy=https://cloudflare.com/cdn-cgi/trace&colo=SEA
  ```
  Cette URL force la requête à être traitée par le datacenter de Seattle (SEA).

- **Limitation** :  
  Cloudflare a patché cette faille, rendant l’outil obsolète. Cependant, des techniques basées sur l’utilisation de VPN permettent encore de contourner l’orientation anycast.

---

## 4. Cas d’Utilisation et Scénarios d’Attaque

### 4.1 Scénario sur Namecheap

Pour une première validation de la méthode, le favicon de Namecheap a été utilisé. Ce favicon, accessible via `https://www.namecheap.com/favicon.ico`, est mis en cache par Cloudflare et présente un faible délai de cache (5 minutes).

- **Observation** :  
  Lorsqu’un utilisateur charge le site, le favicon est automatiquement téléchargé.  
  > **Image du favicon en cache :**  
  > ![Favicon Namecheap en cache](https://gist.github.com/user-attachments/assets/8da57801-ae8e-4adf-9a2e-ec6feec6086f)

- **Résultat** :  
  Les résultats du scan montrent que plusieurs datacenters, répartis géographiquement (par exemple Tokyo et Newark), ont mis en cache le favicon, confirmant ainsi le principe de la désanonymisation par cache.

### 4.2 Application Réelle : Signal

Signal, application de messagerie chiffrée réputée pour sa confidentialité, utilise deux CDNs :
- `cdn.signal.org` (CloudFront) pour les avatars.
- `cdn2.signal.org` (Cloudflare) pour les pièces jointes.

#### 4.2.1 Attaque 1-Clic sur Signal

**Processus :**
1. **Envoi de la pièce jointe :**  
   Lorsqu’un utilisateur envoie une pièce jointe (par exemple, une image 1x1), celle-ci est uploadée sur `cdn2.signal.org`.
   
2. **Téléchargement et mise en cache :**  
   Quand le destinataire ouvre la conversation, son appareil télécharge automatiquement l’image.  
   > **Capture d’écran montrant l’upload via Burp :**  
   > ![Capture Burp Signal](https://gist.github.com/user-attachments/assets/51dd8b7c-375c-4bd1-936c-54c338fe6620)
   
3. **Scan du cache :**  
   Un outil en ligne de commande analyse l’URL de la pièce jointe pour identifier les datacenters ayant mis en cache la ressource.  
   > **Résultat du scan :**  
   > ![Scan Datacenters Signal](https://gist.github.com/user-attachments/assets/1ae6102d-263e-4af6-9073-f3665589d753)

**Conclusion :**  
Dans un test effectué depuis New York, l’un des datacenters identifiés était à Newark, NJ, situé à environ 150 miles de la position réelle.

#### 4.2.2 Attaque 0-Clic via Notifications Push sur Signal

**Méthodologie :**
- **Notifications Push :**  
  Signal envoie automatiquement des notifications push contenant une image (la pièce jointe) lorsqu’un message est reçu.
  
- **Impact :**  
  Même si l’utilisateur ne consulte pas la conversation, l’image est téléchargée par le téléphone, activant ainsi le mécanisme de cache.

> **Configuration des notifications push dans Signal :**  
> ![Paramètres Notifications Signal](https://gist.github.com/user-attachments/assets/fed86790-9915-43a2-9d8b-18a7e5edef62)  
> ![Notification Push Exemple](https://gist.github.com/user-attachments/assets/f33a0364-9119-4634-ae0b-4d3af7ee53db)

**Résultat :**  
L’attaque permet de localiser l’utilisateur sans interaction, rendant la méthode « 0-clic » particulièrement pernicieuse.

---

## 4.3 Application Réelle : Discord

Discord, très populaire pour la communication entre gamers, se révèle également vulnérable via le même mécanisme de cache.

#### 4.3.1 Attaque sur Avatars et Emojis dans Discord

**Principe :**
- **Avatars et Emojis :**  
  Les utilisateurs de Discord peuvent personnaliser leurs avatars et utiliser des emojis personnalisés, qui sont chargés via un CDN et mis en cache par Cloudflare.
  
- **Scénario :**  
  En modifiant l’avatar, on génère un hash nouveau et non encore mis en cache. Ensuite, une action (comme une demande d’amitié) déclenche le téléchargement de l’avatar sur l’appareil cible.

> **URL d’avatar dans les notifications push Discord :**  
> `https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}`  
> **Exemple sur le site :**  
> `https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}.png`

#### 4.3.2 GeoGuesser – Automatisation via Bot Discord

**GeoGuesser** est un bot Discord conçu pour automatiser l’ensemble du processus de l’attaque 0-clic sur Discord.

**Fonctionnalités :**
1. **Changement d’avatar automatique :**  
   Le bot modifie l’avatar du compte utilisateur pour générer un nouveau hash.
   
2. **Envoi de demande d’amitié :**  
   La demande d’amitié déclenche une notification push qui force le téléchargement de l’avatar sur l’appareil de la cible.

3. **Scan et géolocalisation :**  
   Le bot utilise une API privée basée sur Cloudflare Teleport (ou via VPN) pour scanner les datacenters qui ont mis en cache l’avatar.  
   Grâce à l’API Google Maps, il calcule le point médian entre les datacenters et dessine des zones d’incertitude.

> **Capture d’écran du bot GeoGuesser en action :**  
> ![GeoGuesser - Test sur Discord CTO](https://gist.github.com/user-attachments/assets/66914f42-880b-4d23-8902-3cb2f3170118)  
> **GIF du processus automatisé :**  
> ![GeoGuesser Animation](https://ninja.dog/KUiqhJ.gif)

**Impact :**  
Les tests réalisés montrent qu’après l’envoi d’une demande d’amitié, le bot peut identifier deux datacenters locaux. Par exemple, pour un test effectué sur Stanislav Vishnevskiy (CTO de Discord), le résultat indiquait une localisation dans un rayon d’environ 300 miles.

---

## 5. Exemples de Code et Automatisation

### 5.1 Extraction d'En-têtes HTTP avec Python

L’exemple suivant montre comment récupérer et analyser les en-têtes d’une réponse HTTP afin d’extraire `cf-ray` et `cf-cache-status`.

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

### 5.2 Script de Scan des Datacenters

Ce script parcourt une liste de datacenters connus pour vérifier la présence du cache d’une ressource via Cloudflare Teleport.

```python
import requests

datacenters = ["SEA", "IAD", "EWR", "LAX", "CDG"]  # Liste de codes de datacenters

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

### 5.3 Pseudo-code du Bot Discord GeoGuesser

Le bot Discord « GeoGuesser » automatise l’attaque 0-clic en combinant changement d’avatar, envoi de demande d’amitié et scan des datacenters pour géolocaliser la cible.

```python
import discord
import asyncio
import random
import requests

client = discord.Client()

def obtenir_image_aleatoire():
    # Générer ou récupérer une image aléatoire pour l'avatar
    # Retourner l'image sous forme de bytes
    with open("avatar_random.png", "rb") as f:
        return f.read()

def envoyer_demande_amitie(target_username):
    # Implémenter la fonction via l'API Discord pour envoyer une demande d'amitie
    pass

def scanner_cache(url, colo):
    proxy_url = f"https://cfteleport.xyz/?proxy={url}&colo={colo}"
    try:
        response = requests.get(proxy_url, timeout=5)
        return response.headers.get('cf-cache-status', 'Inconnu')
    except Exception as e:
        return f"Erreur : {e}"

def calculer_localisation(resultats):
    # Calculer le point médian à partir des datacenters identifiés
    # Retourner une estimation de localisation sous forme de coordonnées ou de description textuelle
    return "Coordonnées estimées (ex. 37.7749° N, 122.4194° W)"

@client.event
async def on_ready():
    print("Bot GeoGuesser actif.")

@client.event
async def on_message(message):
    if message.content.startswith("!geoguesser"):
        try:
            target_username = message.content.split()[1]
        except IndexError:
            await message.channel.send("Usage : !geoguesser <nom_utilisateur>")
            return
        
        # Étape 1 : Modifier l'avatar avec une image aléatoire
        new_avatar = obtenir_image_aleatoire()
        await client.user.edit(avatar=new_avatar)
        
        # Étape 2 : Envoyer une demande d’amitié à la cible
        envoyer_demande_amitie(target_username)
        
        # Étape 3 : Attendre quelques secondes pour la notification push
        await asyncio.sleep(10)
        
        # Étape 4 : Scanner l'URL de l'avatar à partir des datacenters
        avatar_url = f"https://cdn.discordapp.com/avatars/{target_username}/avatarhash"
        resultats = {}
        for colo in ["SEA", "IAD", "EWR"]:
            resultats[colo] = scanner_cache(avatar_url, colo)
        
        localisation = calculer_localisation(resultats)
        await message.channel.send(f"Localisation estimée : {localisation}")

client.run("VOTRE_TOKEN_DISCORD")
```

---

## 6. Médias et Illustrations

### 6.1 Images Issues du Raw de Base

Les images suivantes sont directement issues du document original et illustrent différents aspects techniques et étapes de l’attaque :

1. **En-tête HTTP renvoyé par Cloudflare**  
   ![En-tête Cloudflare](https://gist.github.com/user-attachments/assets/95e1a39a-ed25-4531-9c57-a1b43c616519)

2. **Favicon de Namecheap (utilisé pour la première validation)**  
   ![Favicon Namecheap](https://gist.github.com/user-attachments/assets/8da57801-ae8e-4adf-9a2e-ec6feec6086f)

3. **Capture d’écran de Burp Suite lors du test sur Signal**  
   ![Capture Burp Signal](https://gist.github.com/user-attachments/assets/51dd8b7c-375c-4bd1-936c-54c338fe6620)

4. **Exemple de règle d’interception dans Burp pour Signal**  
   ![Règle d'interception Burp](https://gist.github.com/user-attachments/assets/20a99d9c-ea9e-453d-85b6-13bb8482061e)

5. **Capture d’écran montrant le téléchargement d’une image dans Signal**  
   ![Image Signal Téléchargée](https://gist.github.com/user-attachments/assets/66b4c6f4-3617-4b79-9612-89a90aa7690c)

6. **Résultats du scan de cache montrant plusieurs datacenters**  
   ![Scan Cache Signal](https://gist.github.com/user-attachments/assets/1ae6102d-263e-4af6-9073-f3665589d753)

7. **Paramètres de Notifications Push dans Signal**  
   ![Paramètres Notifications Signal](https://gist.github.com/user-attachments/assets/fed86790-9915-43a2-9d8b-18a7e5edef62)

8. **Exemple de notification push de Signal**  
   ![Notification Push Exemple](https://gist.github.com/user-attachments/assets/f33a0364-9119-4634-ae0b-4d3af7ee53db)

9. **Capture d’écran du test sur Discord (Stanislav Vishnevskiy)**  
   ![Test Discord CTO](https://gist.github.com/user-attachments/assets/66914f42-880b-4d23-8902-3cb2f3170118)

### 6.2 Vidéos et GIFs

Pour illustrer l’automatisation et l’impact de l’attaque, plusieurs médias vidéo sont intégrés :

- **Animation du Bot GeoGuesser en action**  
  ![GeoGuesser Animation](https://ninja.dog/KUiqhJ.gif)

- **Vidéo explicative du fonctionnement global du système**  
  [Voir la vidéo explicative](https://youtu.be/dummyvideo1)  
  *(Lien fictif pour illustration)*

- **Démonstration en temps réel de l’attaque sur Signal et Discord**  
  [Regarder la démonstration](https://youtu.be/dummyvideo2)  
  *(Lien fictif pour illustration)*

---

## 7. Mesures de Protection et Recommandations

Pour limiter les risques d’exploitation de ce type de vulnérabilité, plusieurs recommandations sont proposées :

1. **Désactivation ou restriction du caching pour les contenus sensibles**  
   - Configurer les règles de cache afin d’empêcher le stockage de ressources critiques dans des datacenters accessibles publiquement.

2. **Utilisation de réseaux de confidentialité renforcés**  
   - Préférer l’utilisation de VPN, Tor ou d’autres technologies garantissant un anonymat renforcé lors de la transmission des données.

3. **Modification des paramètres de notifications push**  
   - Adapter les paramètres pour limiter la quantité de données automatiquement téléchargées (par exemple, ne pas inclure d’images dans les notifications).

4. **Revue de la configuration CDN**  
   - S’assurer que les règles anycast et le caching ne divulguent pas d’informations permettant d’inférer la localisation géographique des utilisateurs.

5. **Audit de sécurité régulier**  
   - Réaliser des audits réguliers afin d’identifier et corriger toute vulnérabilité similaire dans l’infrastructure.

---

## 8. Bug Bounty et Réponses des Parties Impactées

### Signal

- **Réaction initiale** :  
  Signal a rejeté le rapport, affirmant que la protection de l’identité relevait de la responsabilité de l’utilisateur, en dépit de leur position en tant que plateforme axée sur la confidentialité.

- **Analyse** :  
  Cette réponse est jugée insuffisante compte tenu du fait que la vulnérabilité permet d’estimer la localisation avec une précision surprenante, contredisant les attentes en matière de confidentialité.

### Discord

- **Réaction initiale** :  
  La sécurité de Discord avait promis d’étudier le problème avant de finalement renvoyer la responsabilité vers Cloudflare.

- **Impact** :  
  L’attaque, notamment via le bot GeoGuesser, démontre que même une attaque quasi indétectable peut être lancée sur n’importe quel utilisateur de Discord.

### Cloudflare

- **Patch et Prime** :  
  Cloudflare a patché la faille utilisée par Cloudflare Teleport et a attribué une prime de 200 $ via leur programme HackerOne. Cependant, la correction ne supprime pas entièrement le risque, car d’autres méthodes (comme l’usage de VPN) permettent de contourner cette limitation.

- **Déclaration finale** :  
  Cloudflare estime que la responsabilité de la désactivation du caching pour les contenus sensibles incombe aux consommateurs du service.

---

## 9. Conclusion

Ce projet met en lumière la complexité et l’interconnexion des systèmes modernes de distribution de contenu. Bien que les CDN tels que Cloudflare offrent d’excellentes performances grâce au caching, ils peuvent également être exploités pour obtenir des informations sensibles sur la localisation des utilisateurs.

Les points clés à retenir :
- **Exploitation par l’analyse des en-têtes HTTP** :  
  Les informations telles que `cf-ray` et `cf-cache-status` permettent d’identifier le datacenter et d’en déduire la localisation.
  
- **Techniques de redirection via Cloudflare Teleport et VPN** :  
  Ces méthodes permettent de forcer le passage des requêtes par des datacenters spécifiques, renforçant ainsi la précision de la géolocalisation.

- **Applications réelles** :  
  Des cas pratiques sur Signal et Discord démontrent la faisabilité d’attaques 1-clic et 0-clic, avec des conséquences potentiellement critiques pour la confidentialité.

Face à ces risques, il est impératif d’adopter des mesures de protection adaptées, de revoir la configuration des systèmes de cache et de sensibiliser les utilisateurs aux dangers liés à l’exposition de leurs données.

---

## 10. Licence

Ce projet est diffusé sous la [Licence MIT](LICENSE).  
Toute utilisation, modification ou distribution doit être conforme aux termes de cette licence.

---

## Annexes Techniques et Documentation Complémentaire

### A. Documentation sur le Caching Cloudflare
- [Documentation Officielle Cloudflare](https://developers.cloudflare.com/cache/)
- [Comportement par défaut du cache](https://developers.cloudflare.com/cache/concepts/default-cache-behavior/)

### B. Ressources sur Anycast et Géolocalisation
- [Introduction à Anycast](https://fr.wikipedia.org/wiki/Anycast)
- [Analyse des risques liés au caching](https://www.example.com/whitepaper-caching)

### C. Liens vers les Dépôts GitHub Utilisés
- **Cloudflare Teleport** : [https://github.com/hackermondev/cf-teleport](https://github.com/hackermondev/cf-teleport)
- **GeoGuesser (Bot Discord)** : [https://github.com/exemple/geoguesser](https://github.com/exemple/geoguesser)

### D. Vidéos et Présentations
- [Présentation complète de l’attaque (YouTube)](https://youtu.be/dummyvideo1)
- [Démonstration en temps réel (YouTube)](https://youtu.be/dummyvideo2)

---

## Historique des Modifications

- **v1.0.0** – Version initiale basée sur la recherche originale.
- **v1.1.0** – Ajout des exemples de code Python et du script de scan.
- **v1.2.0** – Intégration complète des médias (images, GIFs, vidéos) et réorganisation en sections avancées.

---

## Ressources Complémentaires et Lectures Recommandées

1. **Sécurité des CDN et Caching**  
   - Articles académiques sur les vulnérabilités des systèmes de cache.
   - Études de cas sur l’exploitation du caching dans des environnements à haute sécurité.

2. **Techniques d’Anonymisation et de Désanonymisation**  
   - Rapports de recherche sur l’empreinte numérique et la géolocalisation par infrastructure réseau.
   - Guides pratiques sur la protection de la vie privée dans le contexte des réseaux modernes.

3. **Mises à jour des Protocoles Cloudflare**  
   - Suivi des mises à jour et des correctifs publiés par Cloudflare concernant les failles de sécurité.
   - Participation aux forums de sécurité Cloudflare et aux discussions sur HackerOne.

---

## FAQ (Foire Aux Questions)

**Q1 : Comment le système anycast peut-il être exploité pour la désanonymisation ?**  
R1 : En forçant l’acheminement des requêtes via des techniques telles que Cloudflare Teleport ou l’utilisation de VPN, il est possible d’identifier le datacenter exact ayant servi la requête, permettant ainsi de déduire la position géographique de l’utilisateur.

**Q2 : Les notifications push sont-elles toujours vulnérables ?**  
R2 : Oui, tant que les notifications incluent des médias téléchargés automatiquement, elles constituent un vecteur d’attaque potentiel pour le suivi de la localisation.

**Q3 : Quelles mesures peuvent être prises pour se protéger ?**  
R3 : Il est recommandé de désactiver le caching sur les contenus sensibles, d’utiliser des solutions VPN robustes et de revoir les paramètres des notifications push pour limiter les informations transmises.

---

## Remerciements

Le présent document s’appuie sur des travaux de recherche antérieurs et sur des contributions de la communauté de la sécurité. Les outils et scripts présentés ici sont destinés à des fins éducatives et de sensibilisation, et il est rappelé que toute utilisation malveillante est strictement interdite.

---

## Contact et Contribution

Les contributions à ce projet sont les bienvenues. Pour toute suggestion, correction ou demande d’amélioration, merci de créer une _issue_ ou de soumettre une _pull request_ sur le dépôt GitHub.

**Auteurs et Contributeurs :**  
- [ErrorNoName](https://hackerone.com/daniel)  
- Contributeurs divers de la communauté open-source

---

## Annexes Supplémentaires

### Documentation sur Cloudflare Workers
- [Guide officiel Cloudflare Workers](https://developers.cloudflare.com/workers/)

### Exemples d’Attaques Réelles (Rapports HackerOne)
- [Rapport complet Discord](https://gist.github.com/hackermondev/7d9ae6b372159de7b9d3d7bb82a32ed2)

### Diagrammes et Schémas Techniques

**Diagramme de l’Infrastructure CDN et des Flux de Requêtes :**  
```
            +--------------------+
            |  Utilisateur Final |
            +---------+----------+
                      |
                      v
            +--------------------+
            | Datacenter Local   | <-- cf-ray et cf-cache-status
            +---------+----------+
                      |
                      v
            +--------------------+
            |   Cloudflare CDN   |
            +--------------------+
                      |
                      v
            +--------------------+
            | Serveur d'Origine  |
            +--------------------+
```

**Schéma de l’Attaque 0-Clic :**  
```
[Envoi de Notification Push]
            |
            v
[ Téléchargement Automatique de l'Image ]
            |
            v
[ Mise en Cache par Datacenter Local ]
            |
            v
[ Scan des En-têtes HTTP via VPN/Teleport ]
            |
            v
[ Détermination de la Localisation ]
```

---

## Détails Techniques et Explications Avancées

- **Fonctionnement du Caching :**  
  Le caching repose sur la duplication de contenu dans plusieurs datacenters. Cette duplication réduit la latence et permet de servir rapidement les utilisateurs, mais expose des métadonnées exploitables par des attaquants.

- **Cloudflare Workers et IP Interne :**  
  L’utilisation de Cloudflare Workers pour contourner l’orientation anycast repose sur l’utilisation d’une plage d’IP interne (initialement celle de Cloudflare WARP), permettant d’envoyer des requêtes spécifiques à un datacenter.
  
- **Utilisation de VPN pour Contourner les Patches :**  
  Après la correction de la faille par Cloudflare, l’usage de VPN proposant de nombreux points de présence permet de répliquer l’attaque en forçant le passage par différents datacenters.

- **Mécanisme de Géolocalisation via Google Maps API :**  
  En récupérant les codes de datacenters via `cf-ray`, il est possible d’estimer une position en calculant un point médian. Des cercles d’incertitude peuvent être dessinés pour représenter la marge d’erreur dans la localisation.

---

## Perspectives Futures

- **Amélioration de la Sécurité des CDN :**  
  La recherche continue dans ce domaine vise à trouver des compromis entre performance et sécurité, notamment en isolant les informations de géolocalisation des réponses HTTP.

- **Évolutions de Cloudflare et Alternatives :**  
  D’autres fournisseurs de CDN et de services de sécurité pourraient être affectés par des vulnérabilités similaires. Une veille technologique et des audits réguliers sont indispensables pour anticiper et corriger ces failles.

- **Développement de Contre-mesures :**  
  L’implémentation de techniques de chiffrement des métadonnées ou de redirection aléatoire des requêtes pourrait constituer une solution pour limiter l’exploitation des données de cache.

---

## Conclusion Générale

Ce README présente en détail une méthode de désanonymisation par exploitation des systèmes de caching des CDN, notamment via Cloudflare. La documentation inclut des explications théoriques, des schémas techniques, des exemples de code et de nombreux médias pour illustrer chaque étape de l’attaque.

Les techniques présentées démontrent que même des mécanismes conçus pour améliorer la performance peuvent devenir des vecteurs d’exploitation si les précautions adéquates ne sont pas prises. La sensibilisation, l’audit régulier et la mise en place de contre-mesures robustes restent les piliers d’une sécurité efficace dans l’environnement numérique actuel.

---

## Références et Sources

- [Documentation Cloudflare Cache](https://developers.cloudflare.com/cache/)
- [Forum Cloudflare Workers – Anycast](https://community.cloudflare.com/t/how-to-run-workers-on-specific-datacenter-colos/385851)
- [HackerOne – Rapports de Sécurité](https://hackerone.com/)
- [Documentation Discord API](https://discord.com/developers/docs/intro)
- [Guide Google Maps API](https://developers.google.com/maps/documentation)
