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

Le Best of s'ouvre mais dans mes fichiers donc le problème est réglé, cependant j'ai laissé tombé l'idée d'un deuxième graphique.

Amélioration 1 - Normalisation du score

Actuellement, mon score dépend de :
- La résolution de ma vidéo
- la luminosité
Solution : 
- motion_score = np.mean(diff)
au lieu de :
- np.sum(diff)
Ca va rendre mon algorithme plus robuste
Ici le score dépend de la résolution de la vidéo alors qu'avec ce changement, le score devient indépendant de la taille de la vidéo. J'utilise la moyenne des différences.



Amélioration 2 - Détécter les vrais changements de scène

Actuellement j'utilise seulement le mouvement 
je peux ajouter :
- différence d'histogramme couleur, c'est beaucoup plus fiable

Actuellement je détécte les scènes uniquement avec les mouvements mais il éxiste des cas ou : la caméra coupe et ou il y'a pas beaucoup de mouvement :
plan 1 : paysage calme
cut
plan 2 : autre paysage calme

L'algo ne peux pas détécter la coupure
La solution est alors de comparer les couleurs en calculant un histogramme d'image
Dans la boucle : 

gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

J'ajoute : 

hist = cv2.calcHist([gray], [0], None, [256], [0,256])
hist = cv2.normalize(hist, hist).flatten()

Puis compare avec l'histogramme précedent

Avant la boucle: 

J'ajoute : 

prev_hist = cv2.calcHist([prev_gray], [0], None, [256], [0,256])
prev_hist = cv2.normalize(prev_hist, prev_hist).flatten()

Dans la boucle j'ajoute : 

hist_diff = cv2.compareHist(prev_hist, hist, cv2.HISTCMP_BHATTACHARYYA)

Puis : prev_hist = hist

Cela compare la distribution des pixels

Exemple : 
Image A : sombre
Image B : très lumineuse

L'histogramme est donc très différent et il y'a donc une probabilité de cut de la scène.


Amélioration 3 - 
Au lieu de score = mouvement 
je peux faire : score = 0.7 * mouvement + 0.3 * changement image

J'ai regardé sur DA vinci resolve dans les archives et c'est ce que font les vrais systèmes vidéos

Maintenant on a : 
motion_score
hist_diff

On peut les fusionner

je remplace : 
motion_score = np.mean(diff)

par :

motion_score = np.mean(diff)

combined_score = motion_score + (hist_diff * 50)

puis stocke : 

motion_scores.append(combined_score)

au lieu de : motion_scores.append(motion_score)

On multiplie par 50 pour amplifier l'histogramme

Changement total : 
Score final = mouvement + changement de couleur

Je combine donc deux indicateurs visuels :
- La différence pixel par pixel pour mesurer le mouvement
- la distance entre histogrammes pour détécter les changements visuels globaux


## semaine 5 

Un vrai logiciel vidéo génère en général une image représentative du best-of, cela s'apelle une miniature. 
Pour cela, je vais prendre le moment le plus intense, extraire la frame et l'enregistrer comme thumbnail.png

1- On récupère le meilleur moment
Etant donnée que j'ai deja trié les moments par score:

moments = sorted(moments, key=lambda x: x[2], reverse=True)

Le meilleur moment est :

best_moment = moments[0]

2- On crée une fonction pour générer cette miniature

def generate_thumbnail(video_path, moment):

    start_frame = moment[0]

    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    ret, frame = cap.read()

    if ret:
        base_path = Path(__file__).resolve().parent.parent
        thumbnail_path = base_path / "outputs" / "thumbnail.png"

        cv2.imwrite(str(thumbnail_path), frame)

        print("🖼️ Thumbnail généré :", thumbnail_path)

    cap.release()

3- J'apelle la fonction

generate_thumbnail(video_path, moments[0])

Ainsi mon programme génère automatiquement une miniature du moment le plus intense

J'ai mis une nouvelle vidéo pour le test.mp4, ma vidéo dure 1min29. J'avais une erreur lorsque je lancais mon programme.
L’erreur venait du fait que le programme essayait de récupérer trois valeurs (start, end, score) dans chaque moment, alors que la liste utilisée n’en contenait que deux (start, end).
La boucle a donc été corrigée pour ne lire que ces deux valeurs, ce qui correspond aux données réellement stockées dans la liste.



De plus j'ajoute une petite modification dans ma fonction, actuellement j'ai la premiere frame du meilleur moment mais ce n'est pas forcément la meilleur image de la periode sur laquelle est définit le meilleur moment.
Par exemple : Moment fort : 30.96s → 32.53s
La meilleur frame peut etre : 31.84s

je change ma fonction en y ajoutant ces éléments : 

def generate_thumbnail(video_path, moment, motion_array):

    start, end, score = moment

    # frame avec le score maximum dans le segment
    best_frame = start + np.argmax(motion_array[start:end])

    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(best_frame))

    ret, frame = cap.read()

    if ret:
        output_path = Path("outputs/thumbnail.jpg")
        cv2.imwrite(str(output_path), frame)
        print("🖼️ Miniature générée :", output_path)

    cap.release()


J'ajoute motion_array car il contient le score de chaque frame et on l'utilise pour trouver np.argmax(motion_array[start:end]), c'est-a-dire la frame avec le mouvement maximum

## semaine 6

# Ré-adaptation de la génération du best-of

Une première sélection est  réalisée en ajoutant des segments dans le best-of jusqu’à atteindre deux conditions :

un nombre minimal de segments (au moins 5 moments forts),

une durée minimale du best-of correspondant à 20 % de la durée totale de la vidéo.

Cette approche permet de garantir que le best-of contienne suffisamment de contenu intéressant.


video_duration = frame_count / fps 


    min_bestof_duration = video_duration * 0.2 
    min_moments = 5 

    selected_moments = [] 
    current_duration = 0 

    # 1. On ajoute d'abord les moments forts
    for start, end, score in moments:
        segment_duration = (end - start) / fps

        selected_moments.append((start, end))
        current_duration += segment_duration

        if len(selected_moments) >= min_moments and current_duration >= min_bestof_duration:
            break




# Complément avec les segments de scènes

Dans certains cas, les moments forts détectés ne suffisent pas à atteindre la durée minimale fixée. Pour résoudre ce problème, l’algorithme utilise également les coupures de scène détectées précédemment dans la vidéo. Ces coupures permettent de créer des segments supplémentaires qui complètent le best-of jusqu’à atteindre la durée minimale requise.

  Si la durée n'est pas suffisante, on complète avec les segments issus des scene_cuts
  
    if current_duration < min_bestof_duration:
        for start, end in scene_segments:

            # éviter d'ajouter un segment qui chevauche déjà un moment sélectionné
            overlap = False
            for sel_start, sel_end in selected_moments:
                if not (end < sel_start or start > sel_end):
                    overlap = True
                    break

            if not overlap:
                selected_moments.append((start, end))
                current_duration += (end - start) / fps

            if current_duration >= min_bestof_duration:
             break





 # Réorganisation chronologique des segments

Les segments sélectionnés sont initialement triés selon leur score d’intensité. Cependant, pour assurer une cohérence temporelle lors du visionnage, les segments retenus sont ensuite réordonnés selon leur position dans la vidéo. Cette étape garantit que le best-of suit une progression chronologique naturelle.

 Tri chronologique pour garder un best-of cohérent
    selected_moments = sorted(selected_moments, key=lambda x: x[0])



# Fusion des segments proches

Une étape supplémentaire de post-traitement a été ajoutée afin d'améliorer la fluidité du montage. Lorsque deux segments sélectionnés sont séparés par un intervalle très court, ils sont fusionnés en un seul segment plus long. Cette méthode permet d’éviter les micro-coupures trop rapprochées qui pourraient rendre le best-of difficile à suivre visuellement.

on crée une focntion 
 
 def merge_close_segments(segments, max_gap_frames): 
    if not segments:
        return []

    # segments triés par début
    segments = sorted(segments, key=lambda x: x[0])

    merged = [segments[0]]

    for current_start, current_end in segments[1:]:
        last_start, last_end = merged[-1]

        # si l'écart entre les deux segments est petit, on fusionne
        if current_start - last_end <= max_gap_frames:
            merged[-1] = (last_start, max(last_end, current_end))
        else:
            merged.append((current_start, current_end))

    return merged

      #  Fusion des segments trop proches

    merge_gap_seconds = 1.0
    merge_gap_frames = int(merge_gap_seconds * fps)
    selected_moments = merge_close_segments(selected_moments, merge_gap_frames) 

    #  Recalcul de la durée après fusion

    current_duration = 0
    for start, end in selected_moments:
        current_duration += (end - start) / fps

    Je fais le dernier commit de la semaine 6 et je passe a la semaine 7, je suis obligé de faire une modif pour faire un  nouveau commit qui explique ce que j'ai fait avant donc c'est pour ca que j'écris ceci.



    

## semaine 7

Durant cette semaine, je vais m'intéressé a l'analyse audio, ce qui va me permettre d'avoir une analyse bien plus réaliste.

## Etape 1

j'installe moviepy pour extraire l'audio : pip install moviepy

en haut de mon code analyze_video j'ajoute : 

from moviepy import VideoFileClip

## Etape 2 

mon première objectif est de crée un score audio global 

J'ajoute une fonction qui me permet d'ouvrire la vidéo, récupérer l'audio, découper l'audio en petits morceaux synchronisés avec les frames et calculer l'intensité moyenne de chaque morceau :

from moviepy import VideoFileClip
import numpy as np

def compute_audio_scores(video_path, fps):
    video = VideoFileClip(video_path)

    if video.audio is None:
        print("Pas de piste audio détectée")
        return np.array([])

    audio = video.audio.to_soundarray(fps=22050)

    # si stéréo, on moyenne les deux canaux
    if len(audio.shape) > 1:
        audio = np.mean(audio, axis=1)

    samples_per_frame = int(22050 / fps)
    audio_scores = []

    for i in range(0, len(audio), samples_per_frame):
        chunk = audio[i:i + samples_per_frame]

        if len(chunk) > 0:
            energy = np.mean(np.abs(chunk))
            audio_scores.append(energy)

    return np.array(audio_scores)

la fonction retourne une liste de score, plus la valeur est grande, plus le moment a une intensité sonore forte.

## Etape 3

après motion_array = np.array(motion_scores)
j'ajoute : 
audio_array = compute_audio_scores(video_path, fps)

## Etape 5 

Comme les valeurs n'ont pas la meme échelle, il faut les ramener entre 0 et 1

J'ajoute une fonction pour normaliser:

def normalize_signal(signal):
    if len(signal) == 0:
        return signal

    min_val = np.min(signal)
    max_val = np.max(signal)

    if max_val - min_val == 0:
        return signal

    return (signal - min_val) / (max_val - min_val)


Puis dans analyze_video : 

motion_norm = normalize_signal(motion_array)
audio_norm = normalize_signal(audio_array)

## Etape 6 

Je fusionne les deux : 

combined_array = 0.7 * motion_norm + 0.3 * audio_norm

je met 70 pourcent pour l'image et 30 pourcent pour l'audio 
Cela me parait plutot cohérent étant donnée que l'analyse video reste quand meme plus importante.

## Etape 7 

Je remplace motion_array par combined_array ici : 

smoothed_motion = moving_average(motion_array, window_size=7)
Devient : 
smoothed_motion = moving_average(combined_array, window_size=7)