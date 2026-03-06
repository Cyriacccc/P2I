Amélioration 1 - Normaliser le score

Actuellement, mon score dépend de :
- La résolution de ma vidéo
- la luminosité
Solution : 
- motion_score = np.mean(diff)
au lieu de :
- np.sum(diff)
Ca va rendre mon algorithme plus robuste
Ici le score dépend de la résolution de la vidéo alors qu'avec ce changement, le score devient indépendant de la taille de la vidéo. On utilise la moyenne des différences.

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