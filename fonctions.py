#!/usr/bin/env python3
# -*- coding: utf-8 -*-

############################################################################
# .-') _   ('-.  ) (`-.      .-') _                            .-') _      #        
#    ( OO ) )_(  OO)  ( OO ).   (  OO) )                          ( OO ) ) #
#,--./ ,--,'(,------.(_/.  \_)-./     '._ ,-.-')  .-'),-----. ,--./ ,--,'  #
#|   \ |  |\ |  .---' \  `.'  / |'--...__)|  |OO)( OO'  .-.  '|   \ |  |\  #
#|    \|  | )|  |      \     /\ '--.  .--'|  |  \/   |  | |  ||    \|  | ) #
#|  .     |/(|  '--.    \   \ |    |  |   |  |(_/\_) |  |\|  ||  .     |/  #
#|  |\    |  |  .--'   .'    \_)   |  |  ,|  |_.'  \ |  | |  ||  |\    |   #
#|  | \   |  |  `---. /  .'.  \    |  | (_|  |      `'  '-'  '|  | \   |   #
#`--'  `--'  `------''--'   '--'   `--'   `--'        `-----' `--'  `--'   #
#                                 TEAM: F0DEI,F5SWB,F8ASB      #    
############################################################################

import settings as d
import serial
import time
import os
import sys
import struct
import subprocess
import socket
import fcntl
import struct
from datetime import  *
import time
from time import time,sleep
import locale
import mmap
import requests
import configparser, os
try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen
from subprocess import Popen, PIPE
#librairie Speedtest
import speedtest

#partie dashboard
#import urllib.request, urllib.error, urllib.parse
import ssl
url = 'http://rrf.f5nlg.ovh'
#pour lecture fichier de config
import configparser, os
#pour adresse ip
import socket
#pour CPU
import io
#pour json
import json
#Pour ouverture nomenclature
import csv

DEBUG = False

#Variables:
#eof = '\xff\xff\xff'
eof = bytes([0xFF,0xFF,0xFF])
port = 0 
#Chemin fichier Json
Json = '/etc/spotnik/config.json'
icao = '/opt/spotnik/spotnik2hmi_V2/datas/icao.cfg'
#routine ouverture fichier de config
svxconfig = '/etc/spotnik/svxlink.cfg'
config = configparser.RawConfigParser()
config.read(svxconfig)
#reglage audio
import alsaaudio

#************************
#* NOM DE L'APPLICATION *
#************************
def set_procname(newname):
    from ctypes import cdll, byref, create_string_buffer
    libc = cdll.LoadLibrary('libc.so.6')    #Loading a 3rd party library C
    buff = create_string_buffer(len(newname)+1) #Note: One larger than the name (man prctl says that)
    buff.value = newname.encode('utf-8')                 #Null terminated string as it should be
    libc.prctl(15, byref(buff), 0, 0, 0) #Refer to "#define" of "/usr/include/linux/prctl.h" for the misterious value 16 & arg[3..5] are zero as the man page says.

#***************
#* GESTION LOG *
#***************

def debug_on():
    global DEBUG
    DEBUG = True

#Fonction Debug
def log(s, color):
    if DEBUG:
        if color == 'red':
            print ('\x1b[7;30;41m' + 'DEBUG: ' + s + '\x1b[0m')
        elif color == 'blue':
            print ('\x1b[7;34;40m' + 'DEBUG: ' + s + '\x1b[0m')
        elif color == 'yellow':
            print ('\x1b[7;30;43m' + 'DEBUG: ' + s + '\x1b[0m')
        elif color == 'white':
            print ('\x1b[7;30;47m' + 'DEBUG: ' + s + '\x1b[0m')
        elif color == 'none':
            print (s)   

#***************
#* GESTION COM *
#***************

def portcom(portseriel,vitesse):
    global port
    global screentype
    global porthmi
    
    porthmi=portseriel

    port=serial.Serial(port='/dev/'+portseriel,baudrate=vitesse,timeout=1, writeTimeout=1)
    log("Port serie: " +portseriel+" Vitesse: "+vitesse,"white")

    cmdinfo= eof + b'connect' + eof 
    port.write(cmdinfo)

    r = port.read(128)
    
    if b'comok' in r:
        log(r,"white")
        status, unknown1, model, fwversion, mcucode, serialn, flashSize = r.split(b',')
        log('Status: ' + status.split(b' ')[0].decode("utf-8"),"white")
        screentype=model.split(b' ')[0][0:10]
        log('Model: ' + screentype.decode("utf-8"),"white")
        print(screentype.decode("utf-8"))
    else:
        print('\x1b[7;37;41m'+"VOTRE ECRAN N'EST PAS ACCESSIBLE, MERCI DE VERIFIER VOTRE CABLAGE !"+'\x1b[0m')
        sys.exit()

#*************************
#* GESTION ECRAN NEXTION *
#*************************

def reset_hmi():
    global port
    log("Reset HMI ...","white")
    rstcmd=b'rest' + eof
    port.write(rstcmd)

def update_hmi():
    log("MAJ ECRAN HMI","red")
    log(screentype,"white")
    log(porthmi,"white")
    os.system ('python /opt/spotnik/spotnik2hmi_V2/nextion/nextion.py '+'/opt/spotnik/spotnik2hmi_V2/nextion/' +screentype.decode("utf-8") +'.tft '+ '/dev/'+porthmi)

def hmi_read_line():
    global port
    rcv = port.readline()
    myString = str(rcv)
    return myString

#Fonction ecriture texte sur Nextion ex: ecrire(t0.txt,"hello word")
def ecrire(champ,texte):
    wcmd = str.encode(champ)+b'="'+str.encode(texte)+b'"'+ eof
    port.write(wcmd)
    infoserialtxt=champ+"=" +texte
    log(infoserialtxt,"blue")
#Fonction ecriture valeur sur ecran
def ecrire_val(champ,valeur):
    wcmdval = str.encode(champ)+b'='+str.encode(valeur)+ eof
    port.write(wcmdval)
    infoserialval=champ+"=" +valeur
    log(infoserialval,"blue") 
    
#Fonction appel de page
def go_page(choixnompage):
    appelpage = b'page ' + str.encode(choixnompage)+eof
    port.write(appelpage)
    infoserialpage="page " +choixnompage
    log(infoserialpage,"yellow")

#*************************
#* GESTION TEST INTERNET *
#*************************

def get_speed_net():

    servers = []

    s = speedtest.Speedtest()

    downinfo=s.download()
    
    a=round(downinfo/1000000,2)
    ecrire("speednet.t0.txt",str(a))
    log(("Download: "+ str(a)+" Mbit/s"),"white")
    
    upinfo=s.upload()
    b=round(upinfo/1000000,2)
    ecrire("speednet.t1.txt",str(b))
    log(("Upload: " + str(b)+" Mbit/s"),"white")

    res = s.results.dict()
    info= res["client"]

    c =info["isp"]
    ecrire("speednet.t2.txt",str(c))
    log(("Fournisseur: " + str(c)),"white")

    d = info["ip"]
    ecrire("speednet.t3.txt",str(d))
    log(("Adresse IP: "+str(d)),"white")
    
    e = round(res["ping"],2)
    ecrire("speednet.t4.txt",str(e))
    log(("Ping: "+str(e) + " ms"),"white")

#***************************
#* GESTION PARAMETRE AUDIO *
#***************************
     
#recuperation info niveau 
def get_audio_info(interfaceaudio):
    
    templevelOut = subprocess.check_output('amixer -c 0 get ' + interfaceaudio +" -M", shell=True)
    templevelOut =  str(templevelOut).split('[')
    levelOut=templevelOut[1][:-3]

    lIn= alsaaudio.Mixer(control='Mic')
    templevelIn=lIn.getvolume()
    levelIn=str(templevelIn).strip('[]')
    
    log("Lecture du niveau audio In Alsamixer: "+str(levelIn),"white")
    log("Lecture du niveau audio Out Alsamixer: "+str(levelOut),"white")

    ecrire_val("boot.Vtxt_nIn.val",str(levelIn))
    ecrire_val("boot.Vtxt_nOut.val",str(levelOut))


#Fonction reglage des niveaux    
def set_audio(interfaceaudio,levelOut,levelIn):
    lIn= alsaaudio.Mixer(control='Mic')
    levelOutcor = int(levelOut)*1
    os.system('amixer -c 0 set' + " Mic " + str(levelIn) + "%")
    log(("Reglage du niveau audio In: "+str(levelIn)+"%"),"white")
    log((">>>>>>>>>>>>>> INFO" + interfaceaudio),"white")
    os.system('amixer -c 0 set ' + interfaceaudio +" -M "+ str(levelOutcor) + "%")
    log(("Reglage du niveau audio Out: "+str(levelOut)+"%"),"white")

def requete(valeur):
    requetesend = str.encode(valeur)+eof
    port.write(requetesend)
    log(valeur,"blue")

#****************************
#* REQUETE VERSION SOFTWARE *
#****************************

def check_version():
        r =""
        r = requests.get('https://raw.githubusercontent.com/F8ASB/spotnik2hmi_V2/master/version')
        
        versions = r.text.replace("\n","").split(':')
        hmiversion = versions[1]
        log(hmiversion,"white")
        scriptversion = versions[3]
        log(scriptversion,"white")
        ecrire("maj.Txt_Vhmi.txt",hmiversion)
        ecrire("maj.Txt_Vscript.txt",scriptversion)        

#**************************
#* REQUETE INFOS SYSTEMES *
#**************************

def get_cpu_use():

    CPU_Pct=str(round(float(os.popen('''grep 'cpu ' /proc/stat | awk '{usage=($2+$4)*100/($2+$4+$5)} END {print usage }' ''').readline()),2))
    log(("CPU Usage = " + CPU_Pct),"white")
    return(CPU_Pct)
                                                 
def get_disk_space():
    p = os.popen('df -h /')
    i = 0
    while 1:
        i = i +1
        line = p.readline()
        if i==2:
            disk_space=(line.split()[4])
            return(disk_space[:-1] + ' %') 

#********************* 
#* GESTION DEMARRAGE *
#*********************  

#Fonction de control d'extension au demarrage
def usage():
    program = os.path.basename(sys.argv[0])
    print("")   
    print("             "'\x1b[7;37;41m'"****ATTENTION****"+'\x1b[0m')
    print("")   
    print("Commande: python3 spotnik2hmi.py <port> <vitesse>")
    print("Ex: python3 spotnik2hmi.py ttyAMA0 9600")
    print("")
    sys.exit(1)

if len(sys.argv) > 2:
    log('Ok', 'white')
else:
    usage()
#recuperation GPIO en fonction

def get_gpio_ptt():
    global gpioptt
   
    svxconfig = '/etc/spotnik/svxlink.cfg'
    config = configparser.RawConfigParser()
    config.read(svxconfig)

    gpioptt = config.get('Tx1', 'PTT_PIN')
    log(gpioptt, 'white')
    return(gpioptt)

def get_gpio_sql():
    global gpiosql
   
    svxconfig = '/etc/spotnik/svxlink.cfg'
    config = configparser.RawConfigParser()
    config.read(svxconfig)

    gpiosql = config.get('Rx1', 'GPIO_SQL_PIN')
    log(gpiosql, 'white')
    return(gpiosql)

#recuperation frequence dans Json
def get_frequency():
    global frequence
    
    with open(Json, 'r') as c:
        afind= json.load(c)
        frequence=afind['rx_qrg']
        return(frequence)

#recuperation indicatif dans Json       
def get_callsign():
    global indicatif
    with open(Json, 'r') as d:
        afind= json.load(d)
        call=afind['callsign']
        dept = afind['Departement']
        band = afind['band_type']
        indicatif = '(' + dept + ') ' + call + ' ' + band
        return(indicatif)  

#regarde la version Raspberry
def get_revision():

  # Extract board revision from cpuinfo file
    myrevision = '0000'
    try:
        f = open('/proc/cpuinfo', 'r')
        for line in f:
            if line[0:8] == 'Revision':
                length = len(line)
                myrevision = line[11:length-1]
        f.close()
    except:
        myrevision = '0000'

    return myrevision 

#Logo de demarrage

def logo(Current_version):
    print(" ")
    print('\x1b[7;30;43m'+"                                           .-''-.                                " +'\x1b[0m')                                   
    print('\x1b[7;30;43m'+"                                         .' .-.  )  " +'\x1b[0m')
    print('\x1b[7;30;43m'+"                                        / .'  / /" +'\x1b[0m')
    print('\x1b[7;30;47m'+"  ____  ____   ___ _____ _   _ ___ _  _" +'\x1b[7;30;43m'+"(_/   / /"+'\x1b[7;30;47m'+"      _   _ __  __ ___ " +'\x1b[0m')
    print('\x1b[7;30;47m'+" / ___||  _ \ / _ \_   _| \ | |_ _| |/ / " +'\x1b[7;30;43m'+"   / /     "+'\x1b[7;30;47m'+" | | | |  \/  |_ _|" +'\x1b[0m')
    print('\x1b[7;30;47m'+" \___ \| |_) | | | || | |  \| || || ' /  " +'\x1b[7;30;43m'+"  / /  "+'\x1b[7;30;47m'+"     | |_| | |\/| || | " +'\x1b[0m')
    print('\x1b[7;30;47m'+"  ___) |  __/| |_| || | | |\  || || . \ " +'\x1b[7;30;43m'+"  . '       "+'\x1b[7;30;47m'+" |  _  | |  | || | " +'\x1b[0m')
    print('\x1b[7;30;47m'+" |____/|_|    \___/ |_| |_| \_|___|_|\_\ " +'\x1b[7;30;43m'+"/ /    _.-')"+'\x1b[7;30;47m'+"|_| |_|_|  |_|___|" +'\x1b[0m')
    print('\x1b[7;30;43m'+"                                       .' '  _.'.-'' " +'\x1b[0m')
    print('\x1b[7;30;43m'+"                                      /  /.-'_.'          Version:" + d.versionDash +'\x1b[0m')                
    print('\x1b[7;30;43m'+"                                     /    _.'  TEAM:"+ '\x1b[0m' +'\x1b[3;37;44m' + "/F0DEI"+ '\x1b[0m' +'\x1b[6;30;47m' + "/F5SWB"+ '\x1b[0m' + '\x1b[6;37;41m' + "/F8ASB"+ '\x1b[0m')               
    print('\x1b[7;30;43m'+"                                    ( _.-'              " +'\x1b[0m')             


#********************** 
#* GESTION ENVOI DTMF *
#**********************  

def dtmf(code):
    print(d.version)
    if d.version == '2.0':
        b = open('/tmp/svxlink_dtmf_ctrl_pty', 'w')
    else:
        b = open('/tmp/dtmf_uhf', 'w')

    b.write(code)
    log(('code DTMF: ' + code), 'white')
    b.close()

#***************************
#*  RECHERCHE PRENOM OM FR *
#***************************

def prenom(Searchcall):

    callcut = Searchcall.split (' ')
    Searchprenom = callcut[1]
    print(Searchprenom)
    lines = csv.reader(open('amat_annuaire.csv', 'rb'), delimiter=';')

    for indicatif,nom,prenom,adresse,ville,cp in lines:
        if indicatif==Searchprenom:
            print(prenom)                   

#***************************
#*  ENVOI COMMANDE SHELL   *
#***************************

#Fonction envoyer des commande console
def console(cmd):
    p = Popen(cmd, shell=True, stdout=PIPE)
    out, err = p.communicate()
    return (p.returncode, out, err)

#**************** 
#* GESTION WIFI *
#****************

#Fonction Wifi ECRITURE
def wifi(wifiid,wifipass):
    #ecriture fichier /etc/NetworkManager/system-connections/SPOTNIK
    confwifi = '/etc/NetworkManager/system-connections/SPOTNIK'

    log("Ecriture fichier SPOTNIK + fichier Gui","yellow")
    cfg = configparser.ConfigParser()
    cfg.read(confwifi)
    cfg.set('connection', 'id', wifiid)
    cfg.set('wifi', 'ssid', wifiid)
    cfg.set('wifi-security', 'psk', wifipass)
    cfg.write(open(confwifi, 'w'))

    #lecture de donnees JSON
    with open(Json, 'r') as f:
        config = json.load(f)
    config['wifi_ssid'] = wifiid
    config['wpa_key'] = wifipass
    #ecriture de donnees JSON
    with open(Json, 'w') as f:
        json.dump(config, f)
 
#Fonction ecriture wifi RPI3B+
def wifi_3bplus(ssid,password):
    pathwpasupplicant = '/etc/wpa_supplicant/'
    log('Ecriture fichier wpa_supplicant.conf + fichier Gui', 'yellow')

    #lecture de donnees JSON
    with open(Json, 'r') as f:
        config = json.load(f)
    config['wifi_ssid'] = ssid
    config['wpa_key'] = password
    #ecriture de donnees JSON
    with open(Json, 'w') as f:
        json.dump(config, f)    

    header4 = '    ssid="' + ssid + '"'
    header5 = '    psk="' + password + '"'

#Sauvegarde de wpa_supplicant.conf existant et renommage en wpa_supplicant.conf.old
    os.rename(pathwpasupplicant + 'wpa_supplicant.conf', pathwpasupplicant + 'wpa_supplicant.conf.old')
#creation d'un nouveau fichier wpa_supplicant.conf.new
    fichier = open(pathwpasupplicant + 'wpa_supplicant.conf.new', 'a')
    lines ='%s \n %s \n %s \n %s \n %s \n %s \n %s \n' % (d.header1, d.header2, d.header3, header4, header5, d.header6, d.header7)
    fichier.write(lines)
    fichier.close()
#renommage du ficher wpa_supplicant.conf.new en wpa_supplicant.conf
    os.rename(d.pathwpasupplicant + 'wpa_supplicant.conf.new', pathwpasupplicant + 'wpa_supplicant.conf')
    
#********************
#*  RECHERCHE METEO *
#********************

#Fonction recherche de nom de ville selon code ICAO
def get_city():
    #lecture valeur icao dans config.json       
        with open(Json, 'r') as b:
            afind = json.load(b)
            airport = afind['airport_code']
            #lecture ville dans fichier icao.cfg        
            icao2city = configparser.RawConfigParser()
            config.read(icao)
            Result_city = config.get('icao2city', airport)
            print (Result_city)
            #city= '"'+Result_city+'"'
            ecrire('meteo.t0.txt', str(Result_city)) 
            print('Aeroport de: ' + Result_city) 

#Fonction Meteo Lecture des donnees Metar + envoi Nextion
def get_meteo():
    #recherche code IMAO dans config.json
    with open(Json, 'r') as b:
        afind = json.load(b)
        airport = afind['airport_code']
        #Info ville Aéroport
        log(('Le code ICAO est: ' + airport), 'white')
        get_city()
        fichier = open('/tmp/meteo.txt', 'w')
        fichier.write('[rapport]')
        fichier.close()
        result = console('/opt/spotnik/spotnik2hmi_V2/python-metar/get_report.py ' + airport + '>> /tmp/meteo.txt')
        log(str(result), 'white')
        #routine ouverture fichier de config
        config = configparser.RawConfigParser()
        config.read('/tmp/meteo.txt')
        #recuperation indicatif et frequence
        pression = config.get('rapport', 'pressure')
        temperature = config.get('rapport', 'temperature')
        rose = config.get('rapport', 'dew point')
        buletin = config.get('rapport', 'time')
        buletin = config.get('rapport', 'time')
        heure = buletin.split(':')
        heure = heure[0][-2:] + ':' + heure[1] + ':' + heure[2][:2]
        log((pression[:-2]), 'white')
        log(rose, 'white')
        log(temperature,"white")
        ecrire('meteo.t1.txt', str(temperature))
        ecrire('meteo.t3.txt', str(heure))
        ecrire('meteo.t4.txt', str(rose))
        Pression = pression[:-2] + 'hPa'
        ecrire('meteo.t2.txt', str(Pression))
