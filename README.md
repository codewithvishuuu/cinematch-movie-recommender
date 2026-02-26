# 🍿 CineMatch — AI Movie Recommendation System

<p align="center">
  <b>Smart movie recommendations powered by Machine Learning & Streamlit</b>
</p>

<p align="center">
  <a href="https://cinematch-movie-recommender-bqzsppgvepmahksda8qxg9.streamlit.app/#popular-movies">
    <img src="https://img.shields.io/badge/🚀 Live Demo-Streamlit App-ff4b4b?style=for-the-badge">
  </a>
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge">
  <img src="https://img.shields.io/badge/ML-ScikitLearn-orange?style=for-the-badge">
  <img src="https://img.shields.io/badge/UI-Streamlit-red?style=for-the-badge">
</p>

---

## 🎬 Live App

👉 https://cinematch-movie-recommender-bqzsppgvepmahksda8qxg9.streamlit.app/#popular-movies

---

## ✨ Overview

**CineMatch** is an AI-powered movie recommendation web application that suggests similar movies using a content-based filtering approach.
It analyzes genres, keywords, and story elements to recommend movies instantly with posters, ratings, and descriptions.

The app features a modern UI with dark/light mode and is fully deployed on Streamlit Cloud.

---

## 🔥 Features

✔️ Content-Based Movie Recommendation System
✔️ Fast Movie Search with Suggestions
✔️ Popular Movies Section
✔️ Dark / Light Mode UI
✔️ OMDb API Integration
✔️ Clean Responsive Layout
✔️ Deployed Online using Streamlit

---

## 🧠 Machine Learning Approach

* Text features processed using **TF-IDF Vectorization**
* Similarity calculated via **Cosine Similarity**
* Model stored using `.pkl` files (Git LFS enabled)
* Poster & rating data fetched dynamically from OMDb API

---

## 🛠️ Tech Stack

* Python
* Streamlit
* Scikit-learn
* Pandas & NumPy
* OMDb API
* Git & Git LFS

---

## 📁 Project Structure

```
app.py              → Main Streamlit UI
recommender.py      → ML Recommendation Logic
omdb_api.py         → Movie API Integration
requirements.txt    → Dependencies
*.pkl               → Trained Model Files
```

---

## ⚙️ Run Locally

Clone repo:

```
git clone https://github.com/codewithvishuuu/cinematch-movie-recommender.git
cd cinematch-movie-recommender
```

Install requirements:

```
pip install -r requirements.txt
```

Run app:

```
streamlit run app.py
```

---

## 🔐 Environment Variables

Add your OMDb API key:

```
OMDB_API_KEY="your_api_key_here"
```

---

## ☁️ Deployment

The app is deployed using **Streamlit Cloud** directly from GitHub.

Steps:

1. Push project to GitHub
2. Connect repository in Streamlit Cloud
3. Select `app.py` as main file
4. Add secrets in Advanced Settings

---

## 👨‍💻 Author

**Vishal Kumar**
GitHub: https://github.com/codewithvishuuu

---

<p align="center">
⭐ If you like this project, consider giving it a star!
</p>
