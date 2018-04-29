#!/usr/bin/python3
# -*- coding: utf8 -*-

## wikikIRC3.py


########################################################################
# This file is part of wikikircandroid3.
#
# wikikircandroid3 is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# wikikircandroid3 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with wikikircandroid3.  If not, see <http://www.gnu.org/licenses/>.
#
# WikikIRC by Olivier Baudu, Anthony Templier for Labomedia September 2011.
# Modified by Sylvain Blocquaux 2012.
# Improved by SergeBlender for Labomedia June 2014.
# olivier arobase labomedia point net // http://lamomedia.net
# Published under License GPLv3: http://www.gnu.org/licenses/gpl-3.0.html
# Modification SergeBlender pour wikikircandroid mars 2018
#
########################################################################


"""
Récupère les modifications en temps réél sur Wikipedia.fr

mybot = MyIRCBot(server_list, channel, nickname, realname, bavard=True)
mybot.start()

Les modifs sont un str:
mybot.wiki_out
"""


import re
from urllib.request import urlopen, Request
import urllib.error
import xml.etree.ElementTree as ET

from irc.bot import SingleServerIRCBot

REPLACE =   [
            "=", "*", "|", "''", "<", ">", "{", "}", "[", "]", "•", "/",
            "listeRecents", "/noinclude",
            "  ", "   ",
            "align ", "left", "valign", "top", "<br", "_"
            ]

FIRST = [
            "=", "[", "{", "#", "<", ":", "!"
        ]

BLACK = [
            "Discussion Utilisateur", "small","#", "rowspan", "liste1",
            "galerie web"
        ]


class MyIRCBot(SingleServerIRCBot):
    """Bot qui récupère les modifications sur Wikipedia FR,
    en ne retournant que les phrases jolies."""
    
    def __init__(self, server_list, channel, 
                       nickname, realname, bavard=True):
        """Doc de SingleServerIRCBot
        - irc_list -- A list of ServerSpec objects or tuples of
                       parameters suitable for constructing ServerSpec
                       objects. Defines the list of servers the bot will
                       use (in order).
        - channel  -- "#wikipedia-fr"
        - nickname -- The bot's nickname.
        - realname -- The bot's realname.
        """
        
        SingleServerIRCBot.__init__(self, 
                                    server_list, 
                                    nickname, 
                                    realname)
                                    
        self.channel = channel
        self.wiki_out = ''
        self.bavard = bavard
        self.address = ""
        self.index = 0
        
    def on_welcome(self, serv, ev):
        """Connection à l'IRC."""
        
        print ("\nConnection sur le canal:", self.channel)
        serv.join(self.channel)
        print ("Connecté\n")

    def on_pubmsg(self, serv, ev):
        """Si message reçu sur l'IRC, met à jour self.wiki_out."""
        
        self.get_address(ev)
        
        if self.address:
            # Liste de str avec les modifs de la page
            liste = self.modifs_in_page()
            self.filtre(liste)
        return self.wiki_out

    def modifs_in_page(self):
        """Retourne une liste de modifications dans la page de
        comparaison de version de wikipedia.
        tag = '<td class="diff-context"><div>'
        liste = data.xpath('//td[@class="diff-context"]/div/text()')
        """
        
        page = self.get_page()

        try:
            root = ET.fromstring(page)

            quoi = root.findall('.//td[@class="diff-context"]/')
            liste = []
            for i in range(len(quoi)):
                liste.append(quoi[i].text)
        except:
            liste = [""]
            
        return liste

    def filtre(self, liste):
        """Filtre la liste de lignes récupérées pour avoir un beau texte."""
        good = []
        for line in liste:
            # Suppression des petites lignes et des lignes vides
            if len(line) > 0:
                if not line[0] in FIRST:
                    for i in REPLACE:
                        line = line.replace(i, ' ')
                        # Suppression d'un expace en premier caractère
                        if len(line) > 0:
                            if line[0] == ' ':
                                line = line[1:]
                    # Suppression des lignes techniques
                    ok = 1
                    for b in BLACK:
                        if b in line:
                            ok = 0
                    if ok:
                        good.append(line)
        if len(good) > 0:
            if len(good[0]) > 40:
                self.wiki_out = good[0]
                if self.bavard:
                    if self.wiki_out:
                        print(self.wiki_out, "\n\n")

    def get_page(self):
        """Retourne le html de la page."""
        try:
            req = Request(self.address)
            # Add header becauce wikipedia expected a navigator
            req.add_header('User-agent', 'WikikIRC-0.4')
        except:
            print("Request impossible")
            page = ''
            
        try:
            handle = urlopen(req)
            page = handle.read()
            handle.close()
        except urllib.error.URLError as e:
            print("Pb urlopen", e)
            page = ''
        except:
            print('Page définitivement introuvable')
            page = ''
            
        return page

    def get_address(self, ev):
        """Met à jour l'adresse de la page modifiée."""
        
        try:
            msg = ev.arguments[0]
            
            # Delete color codes codes and get only text
            message = re.compile("\x03[0-9]{0,2}").sub('', msg)

            # Index de http://
            debut = re.search("https://fr.wikipedia.org", message)
            
            # Je coupe le début inutile
            message = message[debut.start():]
            
            # Index du premier espace après debut
            fin = re.search(" ", message)
            
            # Je coupe la fin
            self.address = message[:fin.start()]

        except:
            self.address = None
            if self.bavard:
                print("Adresse introuvable")
                
        if self.bavard:
            print("Récupération des modifications à l'adresse : {0}".format(
                                                                self.address))


if __name__ == "__main__":
    
    server_list = [("irc.wikimedia.org",  6667)]
                    
    channel = "#fr.wikipedia"
    nickname = "La Labomedia"
    realname = "Syntaxis analysis with Python bot"
    
    print(  "Test", 
            "\n", server_list, 
            "\n", channel, 
            "\n", nickname, 
            "\n", realname)
    
    mybot = MyIRCBot(server_list, channel, nickname, realname, bavard=True)
    mybot.start()
