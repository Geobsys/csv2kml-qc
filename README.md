# Fenêtres temporelles optimales pour une acquisition GNSS en milieu urbain

Ce répertoire contient différents modules python permettant pour une acquisition GNSS de retourner un tableau CSV contenant les fenêtres temporelles optimales pour la réaliser: sont pris en compte l'heure de la journée, le nombre de satellites LOS (line of sight) et un indice qualité DOP (Dilution of precision). Ce calcul est réalisable sur une trajectoire théorique au format KML ou une trajectoire rélle issue d'un GEOSTIX en récupérant les fichiers LOG et rinex de navigation.

## Table des matières
- [Description](#description)
- [Prérequis](#prérequis)
- [Installation](#installation)
- [Utilisation](#utilisation)
- [Paramètres](#paramètres)

## Description

## Prérequis
Certains outils doivent être présents pour faire tourner l'algorithme:

- Git  
- Python  
- simplekml  
- pyproj  
- shapely  
- numpy  
- pandas  
- os  
- fiona  
- argparse  
- re  
- gpsdatetime  
- gnsstoolbox
- tqdm
- contextlib
- concurrent.futures
- tempfile

## Installation

1. Installer les modules:
   ```bash
   pip install simplekml pyproj shapely numpy pandas fiona gpsdatetime gnsstoolbox tqdm contextlib tempfile concurrent.futures
   ```

## Utilisation
Pour tester l'algorithme:

1. Accéder au dossier principal:
   ```bash
   cd CheminDuRepertoire/NomDuRepertoire
   ```
2. Lancer l'outil sur un jeu de données ensg.kml théorique:
   ```bash
   python3 src/csv_to_kml.py test/kml/ensg.kml -it kmltraj --temporal -d 21/03/2025 -start_time 10h00 -end_time 18h00 -dist_sep 0.5 -velocity 1.5 -rn test/rinnex/20250323.rnx -buildings test/shp/buildings_near_ensg.shp -mnt=90 
   ```
3. Lancer l'outil sur un jeu de données 20240223.LOG réel:
   ```bash
   python3 src/csv_to_kml.py test/log/20240223.LOG -it log --temporal -d 23/02/2024 -start_time 13h44 -end_time 14h05 -velocity 2.5 -rn test/rinnex/sept054n.24p -ro test/rinnex/sept054n.24o -buildings test/shp/Buildings.shp 
   ```
Si python3 n'est pas reconnu, il faut mettre le chemin de l'executable python, vous pouvez le trouver depuis la console spyder en tapant : import(sys) et print(sys.executable), pensez à le rajouter au PATH dans vos variables d'environnement.

## Paramètres

### Paramètres d'entrée
Définir les paramètres d'entrée:

| Commande | Nom | Type | Description | Valeur par défaut | Valeurs possibles |
|---------|------|------|-------------|---------------|---------------|
| -it | fichier d'entrée | string | fichier d'entrée de type 'log', ou 'kmltraj' | "log" | ["log", "kmltraj"] |
| -rn | fichier d'entrée | string | chemin et nom du fichier rinex de navigation | '' | fichiers rnx de navigation |
| -ro | fichier d'entrée | string | chemin et nom du fichier rinex d'observations, uniquement pour les trajectoires réelles | '' | fichiers rnx d'observations' |
| -buildings | fichier d'entrée | string | chemin et nom du fichier shapefile issu de la BD topo pour calculer les collisions | '' | fichiers shp |
| -d | paramètre d'entrée | string | jour de l'acquisition (réelle ou théorique) | 01/01/2000 | "dd/mm/yyyy" |
| -start_time | paramètre d'entrée | string | heure de début d'acquisition pour une trajectoire théorique ou réelle | 8h00 | toutes les heures |
| -end_time | paramètre d'entrée | string | heure de fin d'acquisition pour une trajectoire théorique ou réelle | 20h00 | toutes les heures |
| -dist_sep | paramètre d'entrée | float | distance séparant chaque point, permettant de connaître l'heure d'acquisition de chaque point | 5 | toutes les distances |
| -velocity | paramètre d'entrée | float | vitesse en m/s du capteur au sol | 1.5 | toutes les vitesses |
| -mnt | paramètre d'entrée | float | altitude ou altitude moyenne imposée aux Z sur la zone étudiée, par exemple 45 mètres | 0 | valeurs d'élévation possibles |

### Choix du mode en entrée

| Commande| Type | Description | Valeurs possibles |
|---------|------|-------------|-------------------|
| --temporal | booléen | Si False, le code initial de conversion CSV->KML est lancé, sinon le calcul des fenêtres temporelles est lancé | True, False |

### Remarque

Pour les utilisateurs Windows, le chemin du grid IGN peut ne pas être trouvé, il faut modifier cette ligne de code dans le fichier csts.py se trouvant dans le dossier src :

```bash
grid_path = "/".join(location_file.split('/')[:-2]) + "/params/fr_ign_RAF20.tif"
```

Modifier en (par exemple):

```bash
grid_path = "C/dossierDuProjet/params/fr_ign_RAF20.tif"
```









