import cv2
import numpy as np
import csv
from pathlib import Path
import matplotlib.pyplot as plt


def analyze_video(video_path: str):
    """
    Analyse avancée :
    - Lecture frame par frame
    - Calcul de différence entre images
    - Mesure du mouvement
    """
    

    

    cap = cv2.VideoCapture(video_path) #On ouvre la vidéo pour l'analyser
    
    if not cap.isOpened():
        print("❌ Impossible d'ouvrir la vidéo")
        return                                     #Si la vidéo ne s'ouvre pas, on affiche un message d'erreur et on arrête l'analyse

    fps = cap.get(cv2.CAP_PROP_FPS) #On récupère les frames par secondes pour calculer les temps plus tard
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) #On récupère le nombre total de frames pour afficher une barre de progression plus tard

    print("📊 Analyse en cours...")
    print(f"Frames totales : {frame_count}")
    print(f"FPS : {fps}")

    
    
    ret, prev_frame = cap.read() #On lit la première frame pour l'utiliser comme référence pour les suivantes
    if not ret:
        print("❌ Impossible de lire la première frame")
        return                                              #Si on ne peut pas lire la première frame, on affiche un message d'erreur et on arrête l'analyse

    prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY) #On convertit la première frame en niveaux de gris pour faciliter le calcul de la différence avec les frames suivantes

    prev_hist = cv2.calcHist([prev_gray], [0], None, [256], [0,256])
    prev_hist = cv2.normalize(prev_hist, prev_hist).flatten()

    frame_index = 1 #On initialise un index de frame pour suivre notre progression dans la vidéo
    motion_scores = [] #On initialise une liste pour stocker les scores de mouvement calculés pour chaque frame

    while True:
        ret, frame = cap.read()
        if not ret:
            break #Si on ne peut plus lire de frames, on sort de la boucle
        if frame_index % 100 == 0:
            progress = frame_index / frame_count * 100
            print(f"Progression : {progress:.1f}%")

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) #On convertit la frame actuelle en niveaux de gris pour faciliter le calcul de la différence avec la frame précédente

        hist = cv2.calcHist([gray], [0], None, [256], [0,256])
        hist = cv2.normalize(hist, hist).flatten()

        diff = cv2.absdiff(prev_gray, gray) #On calcule la différence absolue entre la frame précédente et la frame actuelle pour mesurer le mouvement
        motion_score = np.mean(diff) #On calcule un score de mouvement en moyennant les valeurs de la différence, plus le score est élevé, plus il y a de mouvement entre les deux frames

        hist_diff = cv2.compareHist(prev_hist, hist, cv2.HISTCMP_BHATTACHARYYA) #On calcule la différence entre les histogrammes de la frame précédente et de la frame actuelle pour mesurer les changements de luminosité ou de contraste, cela peut aider à détecter des coupures de scène même si le mouvement n'est pas très élevé

        combined_score = motion_score + hist_diff * 50 #On combine le score de mouvement avec la différence d'histogramme pour obtenir un score plus robuste qui prend en compte à la fois les changements de mouvement et les changements de luminosité ou de contraste, en multipliant la différence d'histogramme par un facteur pour lui donner plus de poids dans le score final
        motion_scores.append(combined_score) #On ajoute le score combiné à notre liste pour l'analyser plus tard

        
        prev_hist = hist #On met à jour l'histogramme précédent pour la prochaine itération de la boucle, afin de comparer avec le prochain frame

        prev_gray = gray #On met à jour la frame précédente pour la prochaine itération de la boucle
        frame_index += 1 #On incrémente l'index de frame pour suivre notre progression dans la vidéo

    cap.release() #On libère la ressource de la vidéo maintenant que nous avons fini de l'analyser

    motion_array = np.array(motion_scores) #On convertit la liste de scores de mouvement en un tableau numpy pour faciliter les calculs statistiques et l'analyse des données

    mean_motion = np.mean(motion_array) #On calcule la moyenne des scores de mouvement pour avoir une idée générale du niveau de mouvement dans la vidéo
    std_motion = np.std(motion_array) #On calcule l'écart-type des scores de mouvement pour mesurer la variabilité du mouvement dans la vidéo, un écart-type élevé indique que le mouvement varie beaucoup d'une frame à l'autre, tandis qu'un écart-type faible indique que le mouvement est plus constant

    threshold = mean_motion + 2 * std_motion #On définit un seuil de détection de coupures de scène en utilisant la moyenne et l'écart-type des scores de mouvement, les frames dont le score de mouvement dépasse ce seuil seront considérées comme des coupures de scène potentielles
    raw_cuts = np.where(motion_array > threshold)[0] #On trouve les indices des frames dont le score de mouvement dépasse le seuil, ces indices représentent les frames où il y a potentiellement une coupure de scène

    scene_cuts = [] #On initialise une liste pour stocker les indices des coupures de scène finales après filtrage pour éviter les faux positifs causés par des mouvements rapides ou des changements de lumière temporaires
    min_gap = int(fps * 0.5)  # minimum 0.5 seconde entre coupures

    last_cut = -min_gap #On initialise une variable pour suivre la dernière coupure de scène détectée, en la mettant à une valeur négative pour s'assurer que la première coupure potentielle sera acceptée

    for cut in raw_cuts:
        if cut - last_cut >= min_gap:
            scene_cuts.append(cut)
            last_cut = cut #On parcourt les indices des coupures potentielles et on ajoute à la liste finale seulement celles qui sont suffisamment éloignées de la dernière coupure acceptée, cela permet de réduire les faux positifs et d'obtenir une liste plus précise des coupures de scène réelles dans la vidéo

    #On crée une liste de segment pour y ajouter les cut des scènes qui ont un score qui va au dessus du seuil de détéction, cette liste est utile car on pourra prendre des cut de cette liste pour combler le best-of dans le cas ou les moments forts ajouter ne font pas le temps nécessaire lorsqu'ils sont sommés.
    scene_segments = []
    max_scene_duration = 3.0  # secondes max pour une scène ajoutée au best-of
    max_scene_frames = int(max_scene_duration * fps) # On calcule le nombre maximum de frames pour une scène à inclure dans le best-of en multipliant la durée maximale par le nombre de frames par seconde, cela nous permet de tronquer les scènes qui sont trop longues pour éviter d'inclure des segments qui pourraient être moins intéressants ou qui pourraient diluer l'impact du best-of, en utilisant ce critère de durée maximale, nous pouvons nous assurer que le best-of reste dynamique et engageant pour le spectateur, en mettant en avant les moments les plus significatifs sans inclure des scènes trop longues qui pourraient perdre l'attention du spectateur.

    for i in range(len(scene_cuts) - 1):
        start = scene_cuts[i]
        end = scene_cuts[i + 1]

        if end > start:
            # si la scène est trop longue, on la tronque
            if (end - start) > max_scene_frames:
                end = start + max_scene_frames

            scene_segments.append((start, end)) #On crée une liste de segments de scène à partir des indices de coupures de scène, en définissant le début de chaque segment comme l'indice de la coupure actuelle et la fin comme l'indice de la coupure suivante, en vérifiant que la fin est bien après le début pour éviter les segments invalides, et en tronquant les segments qui dépassent la durée maximale définie précédemment pour s'assurer que le best-of reste dynamique et engageant pour le spectateur, en utilisant cette liste de segments de scène, nous pouvons ensuite sélectionner les meilleurs moments à inclure dans le best-of en fonction du score de mouvement et d'autres critères d'analyse.


    print("✅ Analyse terminée")
    print(f"Mouvement moyen : {mean_motion:.2f}")
    print(f"Écart-type : {std_motion:.2f}")
    print(f"Seuil de détection : {threshold:.2f}")
    print(f"Nombre de coupures détectées : {len(scene_cuts)}")


 

    # ===== EXPORT CSV =====
    base_path = Path(__file__).resolve().parent.parent #On utilise pathlib pour construire le chemin vers le dossier d'outputs de manière plus robuste et compatible avec différents systèmes d'exploitation
    output_path = base_path / "outputs" / "scene_cuts.csv" #On définit le chemin complet vers le fichier CSV où nous allons exporter les résultats de l'analyse des coupures de scène, en utilisant le dossier d'outputs pour organiser les fichiers générés par l'application

    with open(output_path, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["frame_index", "time_seconds", "motion_score"])

        for index in scene_cuts:
            time_sec = index / fps
            writer.writerow([index, time_sec, motion_array[index]]) #On ouvre le fichier CSV en mode écriture et on utilise un writer pour écrire les données, on commence par écrire une ligne d'en-tête avec les noms des colonnes, puis on parcourt les indices des coupures de scène détectées et on écrit une ligne pour chaque coupure avec l'index de la frame, le temps en secondes correspondant à cet index (calculé en divisant l'index par le nombre de frames par seconde) et le score de mouvement associé à cette frame, cela permet d'avoir un fichier CSV structuré et facile à analyser ou à visualiser avec d'autres outils

    print(f"📄 Fichier exporté : {output_path}")

        # ===== VISUALISATION =====
    base_path = Path(__file__).resolve().parent.parent #On visualise les résultats de l'analyse en créant un graphe du score de mouvement au fil des frames, en utilisant matplotlib pour tracer le graphe, on définit la taille du graphe et on trace la courbe du score de mouvement, on ajoute une ligne horizontale pour indiquer le seuil de détection, et des lignes verticales pour marquer les coupures de scène détectées, on ajoute des titres et des labels pour rendre le graphe plus lisible, puis on sauvegarde le graphe dans le dossier d'outputs avec un nom de fichier descriptif, cela permet d'avoir une représentation visuelle claire du mouvement dans la vidéo et des moments où des coupures de scène ont été détectées
    plot_path = base_path / "outputs" / "motion_plot.png" #On définit le chemin complet vers le fichier PNG où nous allons sauvegarder le graphe du score de mouvement, en utilisant le dossier d'outputs pour organiser les fichiers générés par l'application

    plt.figure(figsize=(12, 6)) 
    plt.plot(motion_array, label="Motion Score")
    plt.axhline(y=threshold, color='r', linestyle='--', label="Seuil")

    for cut in scene_cuts:
        plt.axvline(x=cut, color='g', linestyle=':', alpha=0.7)

    plt.title("Analyse du Mouvement Vidéo")
    plt.xlabel("Frame Index")
    plt.ylabel("Motion Score")
    plt.legend()

    plt.tight_layout()
    plt.savefig(plot_path)
    plt.close()

    print(f"📈 Graphe sauvegardé : {plot_path}")
        # ===== DÉTECTION DES MOMENTS FORTS =====

    def moving_average(data, window_size=7): #On définit une fonction pour calculer la moyenne mobile d'une série de données, cela permet de lisser les fluctuations du score de mouvement et de mieux identifier les tendances générales, en utilisant une fenêtre de taille spécifiée pour calculer la moyenne des valeurs dans cette fenêtre, on utilise la fonction np.convolve pour appliquer la moyenne mobile à la série de scores de mouvement, en normalisant par la taille de la fenêtre pour obtenir une moyenne correcte, le mode 'same' permet de conserver la même taille que les données d'origine, ce qui facilite l'analyse des résultats par rapport aux indices de frames

        return np.convolve(data, np.ones(window_size)/window_size, mode='same') 

    smoothed_motion = moving_average(motion_array, window_size=7) #On applique la fonction de moyenne mobile au tableau de scores de mouvement pour obtenir une version lissée de ces scores, cela permet de réduire le bruit et les fluctuations temporaires dans les données, ce qui facilite la détection des moments forts où le mouvement est significativement plus élevé que la moyenne générale
    dynamic_threshold = np.mean(smoothed_motion) + 0.7 * np.std(smoothed_motion) # On applique une méthode de seuil dynamique pour identifier les moments forts, en calculant une nouvelle moyenne et un nouvel écart-type à partir des scores de mouvement lissés, et en définissant un seuil qui est plus bas que celui utilisé pour les coupures de scène, cela permet de détecter des moments où le mouvement est élevé mais pas nécessairement au point de constituer une coupure de scène, ce qui peut correspondre à des moments d'action ou d'intérêt dans la vidéo

    high_motion_frames = np.where(smoothed_motion > dynamic_threshold)[0] # On trouve les indices des frames où le score de mouvement lissé dépasse le seuil dynamique, ces indices représentent les moments forts potentiels dans la vidéo, où il y a un niveau de mouvement significatif qui pourrait correspondre à des scènes d'action ou des événements importants

    moments = []
    min_duration = int(fps * 0.5)  # au moins 0.5 seconde

    if len(high_motion_frames) > 0:
        start = high_motion_frames[0]
        prev = start

        for frame in high_motion_frames[1:]:
            if frame - prev > 1:
                if prev - start >= min_duration:
                    segment_score = np.mean(smoothed_motion[start:prev])
                    moments.append((start, prev, segment_score))
                start = frame
            prev = frame

        if prev - start >= min_duration:
             segment_score = np.mean(smoothed_motion[start:prev])
             moments.append((start, prev, segment_score))  

        moments = sorted(moments, key=lambda x: x[2], reverse=True) #On trie les moments forts détectés par score de mouvement décroissant pour identifier les moments les plus significatifs dans la vidéo, cela permet de se concentrer sur les scènes d'action ou les événements les plus importants, en utilisant une fonction de tri qui prend en compte le score de mouvement moyen pour chaque segment identifié, et en triant ces segments du plus élevé au plus bas, ce qui facilite l'analyse et l'export des meilleurs moments de la vidéo
             

        

    print("\n🎯 Moments forts détectés :")
    for start, end, score in moments:
        print(f"- {start/fps:.2f}s → {end/fps:.2f}s | Score : {score:.2f}")   


    print("Moments envoyés à l'export :", moments)



    video_duration = frame_count / fps #On calcule la durée totale de la vidéo en secondes en divisant le nombre total de frames par le nombre de frames par seconde, cela permet d'avoir une référence temporelle pour les segments et les moments forts détectés, et de calculer des durées relatives pour le best-of que nous allons générer, en utilisant cette durée totale pour définir des seuils ou des limites pour la sélection des segments à inclure dans le best-of, afin de créer une compilation qui met en avant les moments les plus significatifs de la vidéo tout en respectant une durée globale raisonnable pour le résultat final
    min_bestof_duration = video_duration * 0.2 #On définit une durée minimale pour le best-of que nous allons générer, en utilisant un pourcentage de la durée totale de la vidéo, cela permet de s'assurer que le best-of contient suffisamment de contenu pour être intéressant et représentatif des moments forts détectés, tout en évitant de créer un best-of trop long qui pourrait perdre l'attention du spectateur, en utilisant cette approche basée sur la durée relative de la vidéo, nous pouvons adapter la longueur du best-of en fonction de la durée totale de la vidéo analysée, ce qui rend notre application plus flexible et adaptée à différents types de vidéos
    min_moments = 5 #On définit un nombre minimum de moments forts à inclure dans le best-of, cela permet de garantir que le best-of contient une sélection suffisante de moments significatifs, même si la durée totale des moments forts détectés est inférieure à la durée minimale définie précédemment, en utilisant ce critère basé sur le nombre de moments, nous pouvons nous assurer que le best-of met en avant une variété de scènes d'action ou d'événements importants, même si la vidéo analysée est relativement courte ou si les moments forts sont concentrés dans une partie spécifique de la vidéo

    selected_moments = [] #On initialise une liste pour stocker les moments forts sélectionnés pour le best-of, en utilisant les critères de durée minimale et de nombre minimum de moments définis précédemment, cela nous permet de construire une sélection de segments qui seront inclus dans le best-of final, en parcourant d'abord les moments forts détectés et en les ajoutant à la liste de sélection tant que les critères ne sont pas encore satisfaits, puis en complétant avec des segments issus des coupures de scène si nécessaire pour atteindre la durée minimale du best-of, cela nous permet de créer un best-of qui met en avant les moments les plus significatifs tout en respectant une durée globale cohérente et engageante pour le spectateur
    current_duration = 0 

    # 1. On ajoute d'abord les moments forts et on s'assure qu'ils respectent les critères de durée et de nombre minimum, en parcourant la liste des moments forts détectés, on ajoute chaque moment à la sélection tant que le nombre de moments sélectionnés est inférieur au nombre minimum défini et que la durée totale des moments sélectionnés est inférieure à la durée minimale du best-of, cela permet de prioriser l'inclusion des moments les plus significatifs dans le best-of, tout en s'assurant que nous avons une base solide de contenu avant de compléter avec d'autres segments si nécessaire, en utilisant cette approche, nous pouvons créer un best-of qui met en avant les moments forts tout en respectant les contraintes de durée et de diversité que nous avons définies pour garantir un résultat final engageant et représentatif de la vidéo analysée.
    for start, end, score in moments:
        segment_duration = (end - start) / fps

        selected_moments.append((start, end))
        current_duration += segment_duration

        if len(selected_moments) >= min_moments and current_duration >= min_bestof_duration:
            break

    # 2. Si la durée n'est pas suffisante, on complète avec les segments issus des scene_cuts
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
    # 3. Tri chronologique pour garder un best-of cohérent
    selected_moments = sorted(selected_moments, key=lambda x: x[0])

    # 4. Fusion des segments trop proches
    merge_gap_seconds = 1.0
    merge_gap_frames = int(merge_gap_seconds * fps)
    selected_moments = merge_close_segments(selected_moments, merge_gap_frames) #On définit une fonction pour fusionner les segments sélectionnés qui sont trop proches les uns des autres, en utilisant un critère de distance en secondes (converti en frames) pour déterminer si deux segments doivent être fusionnés, cela permet de créer un best-of plus fluide et cohérent en évitant d'avoir des coupures trop fréquentes ou des segments très courts qui pourraient diluer l'impact du best-of, en parcourant la liste des segments sélectionnés et en fusionnant ceux qui sont séparés par une distance inférieure au seuil défini, on peut obtenir une liste finale de segments qui représentent les moments forts de la vidéo de manière plus naturelle et engageante pour le spectateur.

    # 5. Recalcul de la durée après fusion
    current_duration = 0
    for start, end in selected_moments:
        current_duration += (end - start) / fps

    print("Segments sélectionnés pour le best-of :", selected_moments)
    print(f"Nombre de segments sélectionnés : {len(selected_moments)}")
    print(f"Durée vidéo : {video_duration:.2f}s")
    print(f"Durée minimum best-of : {min_bestof_duration:.2f}s")
    print(f"Durée best-of généré : {current_duration:.2f}s")

    export_best_of(video_path, selected_moments)
    
    if len(moments) > 0:
        generate_thumbnail(video_path, moments[0], motion_array)
    else:
        print("⚠️ Aucun moment fort détecté, miniature non générée") # On apelle la fonction pour affichier la miniature a codition qu'il existe au moins 1 moment fort

   

def export_best_of(video_path, moments, output_name="best_of.mp4"): #On définit une fonction pour exporter un best-of de la vidéo en utilisant OpenCV pour lire la vidéo originale et écrire un nouveau fichier vidéo qui contient uniquement les segments correspondant aux moments forts détectés, en utilisant les indices de frames des moments forts pour extraire les segments de la vidéo originale, et en combinant ces segments dans un nouveau fichier vidéo avec une qualité et un format appropriés, cela permet de créer un best-of personnalisé qui met en avant les moments les plus significatifs de la vidéo, tout en offrant une expérience de visionnage plus concise et plus engageante pour l'utilisateur
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print("❌ Impossible d'ouvrir la vidéo pour export")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')

    base_path = Path(__file__).resolve().parent.parent
    output_path = base_path / "outputs" / output_name

    out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
    print("Writer ouvert ?", out.isOpened())
    print("FPS:", fps)
    print("Width:", width)
    print("Height:", height)

    print("🎬 Génération du best-of...")

    for start, end in moments:

        cap.set(cv2.CAP_PROP_POS_FRAMES, start)

        for frame_idx in range(start, end):
            ret, frame = cap.read()
            if not ret:
                break
            out.write(frame)

    cap.release()
    out.release()

    print(f"✅ Best-of exporté : {output_path}")

    

def generate_thumbnail(video_path, moment, motion_array):

    start, end, score = moment

    # frame avec le score maximum dans le segment
    best_frame = start + np.argmax(motion_array[start:end])

    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(best_frame))

    ret, frame = cap.read()

    if ret:
        output_path = Path("outputs/thumbnail.png")
        cv2.imwrite(str(output_path), frame)
        print("🖼️ Miniature générée :", output_path)

    cap.release()
# On peut ajouter une fonction pour générer une miniature de la vidéo à partir du moment fort le plus significatif, en utilisant OpenCV pour capturer une frame spécifique de la vidéo correspondant au début du moment fort, puis en sauvegardant cette frame comme une image PNG dans le dossier d'outputs, cela permet d'avoir une représentation visuelle du moment fort le plus important de la vidéo, qui peut être utilisée comme vignette ou aperçu pour le best-of généré.


def merge_close_segments(segments, max_gap_frames): #On définit une fonction pour fusionner les segments qui sont trop proches les uns des autres, en utilisant un critère de distance en frames pour déterminer si deux segments doivent être fusionnés, cela permet de créer un best-of plus fluide et cohérent en évitant d'avoir des coupures trop fréquentes ou des segments très courts qui pourraient diluer l'impact du best-of, en parcourant la liste des segments et en fusionnant ceux qui sont séparés par une distance inférieure au seuil défini, on peut obtenir une liste finale de segments qui représentent les moments forts de la vidéo de manière plus naturelle et engageante pour le spectateur.
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