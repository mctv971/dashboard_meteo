# 🌤️ Dashboard Météo - Projet Collaboratif

Un dashboard Streamlit complet pour afficher des données météorologiques, horoscope, saints du jour et blagues quotidiennes.

## 📁 Structure du Projet

### 🏠 Page d'accueil - **Malcom**
**Fichier:** `dashboard_multipage.py`

- Interface de sélection de ville
- Géolocalisation automatique
- Navigation vers la page de données
- Gestion des villes prédéfinies et recherche personnalisée

### 📊 Page de données - **Adrian**
**Fichier:** `donnees_page.py`

- Affichage des données récupérées
- Interface utilisateur pour les 4 types de données :
  - 🌤️ Données météorologiques
  - 📿 Saints du jour
  - 🔮 Horoscope personnalisé
  - 😄 Blague du jour

### 🔧 Module de données
**Fichier:** `requete_page1.py`

- Fonctions de récupération de données depuis les APIs
- Traitement et formatage des données
- Retour de dictionnaires Python (pas de sauvegarde JSON)

## 🚀 Lancement du Dashboard

```bash
# Installer les dépendances
pip install -r requirements.txt

# Lancer le dashboard
streamlit run dashboard_multipage.py
```

## 👥 Répartition des Tâches

| Développeur | Responsabilité | Fichier Principal |
|-------------|----------------|-------------------|
| **Malcom** | Page d'accueil et navigation | `dashboard_multipage.py` |
| **Adrian** | Page de données et affichage | `donnees_page.py` |

## 🛠️ Fonctionnalités

### Page d'accueil (Malcom)
- ✅ Sélection de ville par liste prédéfinie
- ✅ Recherche personnalisée de ville
- ✅ Géolocalisation automatique (ville → coordonnées)
- ✅ Validation des données de géolocalisation
- ✅ Navigation fluide vers la page de données
- ✅ Interface utilisateur intuitive

### Page de données (Adrian)
- ✅ Récupération de données météo en temps réel
- ✅ Affichage des saints du jour
- ✅ Horoscope personnalisé (sélection du signe)
- ✅ Blague quotidienne
- ✅ Progress bar pour le suivi
- ✅ Organisation en colonnes et sections expandables
- ✅ Gestion des erreurs et feedback utilisateur

## 📋 APIs Utilisées

- **Open-Meteo** : Données météorologiques
- **Nominis** : Saints du jour
- **Prokerala** : Horoscope quotidien
- **Blagues API** : Blagues aléatoires

## 🔄 Workflow Collaboratif

1. **Malcom** travaille sur l'interface d'accueil et la navigation
2. **Adrian** se concentre sur l'affichage et le traitement des données
3. Les deux pages communiquent via `st.session_state`
4. Module `requete_page1.py` partagé pour la récupération de données

## 📦 Dépendances

Voir `requirements.txt` pour la liste complète des bibliothèques nécessaires.

## 🎯 Objectifs

- [x] Séparation claire des responsabilités
- [x] Interface utilisateur moderne et responsive
- [x] Récupération de données en temps réel
- [x] Navigation fluide entre les pages
- [x] Code modulaire et maintenable

---

**Note :** Chaque développeur peut travailler indépendamment sur sa partie tout en maintenant la cohérence de l'ensemble du projet.