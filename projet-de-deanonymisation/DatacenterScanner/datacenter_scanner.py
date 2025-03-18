#!/usr/bin/env python3
"""
DatacenterScanner - Scanner de cache via Cloudflare Teleport

Ce script interroge plusieurs datacenters (via l'outil Cloudflare Teleport)
pour vérifier si une ressource est présente dans le cache d'un datacenter spécifique.
"""

import requests

# Liste de codes de datacenters à scanner
DATACENTERS = ["SEA", "IAD", "EWR", "LAX", "CDG"]

def scan_datacenter(url, colo):
    """
    Construit l'URL de requête via Cloudflare Teleport pour un datacenter spécifique,
    envoie la requête et renvoie l'état du cache.

    :param url: URL de la ressource à scanner
    :param colo: Code du datacenter ciblé (ex. "SEA" pour Seattle)
    :return: État du cache (cf-cache-status) ou message d'erreur
    """
    proxy_url = f"https://cfteleport.xyz/?proxy={url}&colo={colo}"
    try:
        response = requests.get(proxy_url, timeout=5)
        return response.headers.get("cf-cache-status", "Inconnu")
    except Exception as e:
        return f"Erreur : {e}"

if __name__ == '__main__':
    url = input("Entrez l'URL à scanner (ex. https://www.namecheap.com/favicon.ico) : ")
    print("Scan des datacenters en cours...\n")
    for colo in DATACENTERS:
        status = scan_datacenter(url, colo)
        print(f"Datacenter {colo} - cf-cache-status : {status}")
