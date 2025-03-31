# Fenêtres temporelles optimales pour une acquisition GNSS en milieu urbain

Ce répertoire contient différents modules python permettant pour une acquisition GNSS de retourner un tableau CSV contenant les fenêtres temporelles optimales pour la réaliser: sont pris en compte l'heure de la journée, le nombre de satellites LOS (line of sight) et un indice qualité DOP (Dilution of precision). Ce calcul est réalisable sur une trajectoire théorique au format KML ou une trajectoire rélle issue d'un GEOSTIX en récupérant les fichiers LOG et rinex de navigation.

## Table des matières

- [Introduction](#Introduction)
- [Buildings](#Buildings)
- [Ephémérides](#Ephémérides)
-
- [Help](#Help)


# Introduction

Premièrement, il faut télécharger le code et installer toutes les dépendances citées dans le fichier README.

Après l'installation, il faudra préparer les fichiers nécessaires à l'éxecution du programme:

- Un fichier représentant la trajectoire sur laquelle réaliser le traitement, soit au format KML (dessinée sur google EARTH ou un SIG), soit au format LOG (issue d'une acquisition avec Géostix).
- Pour calculer les collisions entre les bâtiments et les droites (géostix, satellites), un fichier au format shapefile issue de la [BD-TOPO](https://geoservices.ign.fr/bdtopo) recouvrant la zone d'étude.
- Pour calculer les éphémérides des satellites, un fichier RINEX de navigation quelque soit le type de trajectoire et récupérable sur le site de la [NASA](https://cddis.nasa.gov/Data_and_Derived_Products/GNSS/broadcast_ephemeris_data.html) en précisant le jour de l'année (par exemple le 84ème jour de l'année) et en prenant dans le bon dossier (24p pour les RINEX de navigation de l'année 2024) et un fichier RINEX d'observation pour les trajectoires réelles (issu du Géostix).

## Premier exemple

1. Maintenant, lancez l'invite de commande et placez vous dans le répertoire du projet:
    ```bash
    cd CheminDuRepertoire/NomDuRepertoire
    ```

2. Lancez la commande suivante comme expliquer dans le README pour tester le code sur une trajectoire thérorique autour de l'ENSG:
   ```bash
   python3 src/csv_to_kml.py test/kml/ensg.kml -it kmltraj --temporal -d 21/03/2025 -start_time 10h00 -end_time 18h00 -dist_sep 0.5 -velocity 1.5 -rn test/rinnex/20250323.rnx -buildings test/shp/buildings_near_ensg.shp -mnt=90 
   ```
(voir le README pour la commande trajectoire réelle)

Votre tableau récapitulatif est enregistré dans le répertoire du projet au format CSV.

# Buildings

Le programme permet d'intégrer des bâtiments recouvrant la zone d'étude. Cette étape nécessite de fournir un fichier  au format Shapefile issu de la [BD-TOPO](https://geoservices.ign.fr/bdtopo), attention à ne choisir que des dates post 2024 car avant 2024 les fichiers n'ont pas le même format.

1. Par défaut, le programme sélectionne les bâtiments dans un rectangle contenant tous les points avec une certaine marge. Avec la commande "-margin", cette marge peut être modifiée.

2. Les bâtiments sont modélisés par des pavés, le calcul des rayons de collision reste donc approximatif, il aurait fallu modéliser chaque face de chaque bâtiment mais ça aurait augmenter le temps de calcul.

3. Bien spécifier le chemin du dossier "shp" ainsi que le fichier Shapefile à l'intérieur, sinon le premier fichier sera sélectionné.

# Ephémérides

Pendant les acquisitions pour une trajectoire réelle, sont récupérés via le géostix les fichiers RINEX de navigation et d'observations, avec ceux-ci on peut déterminer les satellites visibles depuis chaque point avec leurs coordonnées.

# Help 

Pour avoir des informations sur les commandes et leur valeur par défaut, se référer au README ou utiliser la commande '-h' ou '--help' :
```bash 
python3 src/csv_to_kml.py -h
```
