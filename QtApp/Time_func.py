import os
import time

def time_init():
    os.environ['TZ'] = 'US/Eastern'
    time.tzset()

def time_string():
    #H = Heure, M = Minute, S = Seconde
    #Y = Annee, m = Mois , d = Journee
    return time.strftime('%d%m%Y_%H-%M-%S')

def only_time_string():
    #H = Heure, M = Minute, S = Seconde
    #Y = Annee, m = Mois , d = Journee
    return time.strftime('%H-%M-%S')
