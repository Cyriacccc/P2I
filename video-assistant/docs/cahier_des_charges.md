# Comment obtient t'on le score d'une frame?

Le score d'une frame représente la quantité de mouvement entre cette frame et la précedente, il ne mesure pas le contenu, il mesure uniquement le changement visuel.

Sur quoi se base le calcul?

La différence pixel par pixel entre deux images consécutives

Etapes précises du calcul

1- Conversion en niveaux de gris
gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
 Cela permet de réduire la compléxité (1 canal au lieu de 3)
 Le mouvement dépend surtout de la luminosité
 Optimisation des performances

2- Calcul de la différence absolue
diff = cv2.absdiff(prev_gray, gray)
pour chaque pixel:
diff(x,y) = |It(x,y) - It-1(x,y)|
It = intensité du pixel a l'instant t
It-1 = intensité du pixel a l'instant t-1

3- Somme de toutes les différences
motion_score = np.sum(diff)
On additionne toutes les différences
Score = somme(|It(x,y)-It-1(x,y)|)

Interprétation du score :
Score faible - image presque identique - peu de mouvement 
Score élevé - changement important - mouvement ou coupure


Pour l'instant le score mesure : 

- Variation globale
- Mouvement d'objets
- Changement de caméra
- Coupure brutale

A venir : 
l'objectif est qu'il mesure :
- Le sens de l'image
- l'importance narrative
- L'audio

On utilise la somme car c'est simple, rapide et suffisant pour détecter les pics 
On aurait pu utiliser :
- Moyenne 
- Historgramme 

Pourquoi ca marche bien ?

Une coupure de scène - presque tous les pixels changent 
Une action rapide - grande zone en mouvement 
Une scène calme - peu de variation



# Objectif de la segmentation

Transformer [score_frame1, score_frame2, ...] en [(debut1, fin1), (debut2, fin2), ...]

On passe d'un signal brut a des segments temporel exploitables

1- On recoit le signal de mouvement 
motion_array = [1000, 1200000, ...]
Chaque valeur = intensité du changement entre deux frames
C'est un signal temporel

2 - Lissage du signal
smoothed = moving_average(motion_array)
Pourquoi?
Le signal brut est bruité:
- micro-variations
- bruit caméra
- compression vidéo
- petits mouvements inutiles

On applique donc une moyenne glissante : 
np.convolve(data, np.ones(window_size)/window_size, mode ='same')
Concrètement , si window = 7, Chaque point devient la moyenne des 7 voisins
Avant : 2, 3, 50, 4, 3
Après : plus stable

3 - Calcul du seuil adaptatif
Code : threshold = mean + 0.7 * std
Pourquoi pas un seuil fixe?
parce que chaque vidéo est différente :
Sport - très dynamique 
Vlog - très calme
Intervieuw - statique (presque)

mean = niveau moyen d'activité
std = variabilité du mouvement 

si un point dépasse threshold, il est anormalement élevée
C'est une détéction basé sur la dispersion

4- détection des frames actives 
high_motion = np.where(smoothed > threshold)[0]
On récupère les indices des frames au dessus du seuil

5- Regroupement en segments
On parcourt les indices : 
if frame - prev > 1
Si deux frames ne sont pas consécutives:
on termine un segment 
on en commence un nouveau

 exemple :
 [5, 6, 7, 8] = segment 1
 [20, 21, 22] = segment 2

 On transforme donc des points en intervalles

6- Filtrage par durée minimale 
min_duration = int(fps*0.5)
on impoose minimum 5s
Sinon on aurait : 
- micro-pics
- faux positifs
- segments trop courts

on garde seulement : si (fin-debut) >= min_duration

7- Résultat final
On obtient : [(9, 29), (32, 51)]
Ce sont des intervalles de frames

