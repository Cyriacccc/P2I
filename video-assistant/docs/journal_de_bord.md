# Journal de bord

L’objectif du projet est de créer un système capable d’analyser automatiquement une vidéo et d’en extraire les moments les plus dynamiques, afin de générer un résumé automatique (best-of).

L’idée est d’automatiser ce que ferait un humain :

Regarder la vidéo

Repérer les passages intéressants

Couper et assembler les meilleurs moments



Le projet repose sur une idée simple :

Plus il y a de mouvement entre deux images consécutives, plus la scène est susceptible d’être “intense” ou “intéressante”.

On exploite donc :

La différence entre frames

Des statistiques (moyenne + écart-type)

Un filtrage temporel




## Semaine 1
- Création de l’architecture du projet
- Mise en place de l’environnement Python
- Premiers tests d’analyse vidéo

Observations :
- j'ai reussi a analyser la video en ayant les fps, les mouvements, les coupures...

– Lecture de la vidéo

Dans analyze_video() :

cap = cv2.VideoCapture(video_path)

On ouvre la vidéo avec OpenCV.

On récupère :

le nombre total de frames

le FPS (images par seconde)

## semaine 2
- j'ai obtenue un graphique qui représente le -motion score en fonction du Frame index.
Chaque points correspond a la différence entre la frame n et la frame n-1.(Valeur faible = peu de changement visuel et valeur élévée = fort changement visuel)
- la courbe rouge représente la moyenne + 2*ecart type
ce qui permet de séléctionner statistiquement les anomalies
- La ligne verte correspond au coupures détéctés:
Ce sont les frames ont motion_score > treshold et ecart temporel > min_gap
On a donc :
Une modélisation du mouvement par différences d'images 
L'utilisation d'un seuil statistique adaptatif

On a un pic a 2,2*10E7 = changement brutal dans l'image

Conclusion : 
Le graphique montre une distribution normale du mouvement 
Une anomalie extreme
Un seuil adaptatif cohérent
une detection propre et unique

## semaine 3
J'essaie de générer un best of de ma video a partir des paramètres étudiés dans mon fichier de code analyse de la video. mais sans succés

Concernant le best of :

On détecte les frames au dessus du seuil:
high_motion_frames = np.where(smoothed_motion > dynamic_threshold)[0]

Puis on regroupe les frames consécutives en segments : 
moments.append((start, end))

On impose une durée minimale : 
min_duration = int(fps * 0.5)
Pour éviter les micro-évenements

Pour chaque segment : 
cap.set(cv2.CAP_PROP_POS_FRAMES, start) ouverture de la video

Puis on écrit les frames dans un nouveau fichier:
out.write(frame)

On obtient une nouvelle vidéo contenant uniquement les moments forts.

problème je n'arrive pas a ouvrire le best of


## semaine 4

Il faut que le best of s'ouvre

il faut que je génere un graphique de la meme manière que pour la video d'origine, cela me permettra de valider visuellement le fonctionement de mon best of
