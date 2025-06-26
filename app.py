import time
import streamlit as st
import pickle
import pandas as pd
import requests


st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(to right, #1CB5E0, #000046);
        color: white;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# Caching dictionary to avoid repeated poster fetching
poster_cache = {}

def fetch_poster(movie_id):
    if movie_id in poster_cache:
        return poster_cache[movie_id]

    api_key = "3b4b10b60d9f6fdb1991e6440576b691"
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }

    for attempt in range(3):
        try:
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 429:
                print("Rate limited. Waiting 2s...")
                time.sleep(2)
                continue
            response.raise_for_status()
            data = response.json()
            poster_path = data.get('poster_path')
            if poster_path:
                full_url = "https://image.tmdb.org/t/p/w500/" + poster_path
            else:
                full_url = "https://via.placeholder.com/300x450?text=No+Poster"
            poster_cache[movie_id] = full_url
            return full_url
        except Exception as e:
            print(f"[Attempt {attempt+1}] Error for movie_id {movie_id}: {e}")
            time.sleep(1)  # backoff retry
    return "https://via.placeholder.com/300x450?text=Error"



def recommend(movie):
    movie_index = movies[movies['title'] == movie].index[0]
    distances = similarity[movie_index]
    movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

    recommended_movies = []
    recommended_movies_posters = []

    for i in movies_list:
        movie_id = movies.iloc[i[0]].movie_id
        recommended_movies.append(movies.iloc[i[0]].title)
        time.sleep(1.2)
        poster_url = fetch_poster(movie_id)
        time.sleep(0.3)  # Adjust delay to avoid TMDB rate limit
        recommended_movies_posters.append(poster_url)

    max_retries = 3
    for attempt in range(max_retries):
        need_retry = False
        for i in range(5):
            if "placeholder.com" in recommended_movies_posters[i]:
                print(f"Retrying for '{recommended_movies[i]}' (Attempt {attempt + 2})")
                movie_id = movies[movies['title'] == recommended_movies[i]].movie_id.values[0]
                time.sleep(1.2)
                poster = fetch_poster(movie_id)
                recommended_movies_posters[i] = poster
                if "placeholder.com" in poster:
                    need_retry = True
        if not need_retry:
            break

    return recommended_movies, recommended_movies_posters


# Load data
movies_dict = pickle.load(open('movies_dict.pkl', 'rb'))

movies = pd.DataFrame(movies_dict)
similarity = pickle.load(open('similarity.pkl', 'rb'))

# Streamlit UI
st.title('🎬Movie Recommendation System')

selected_movie_name = st.selectbox("Select a Movie", movies['title'].values)

if st.button("Recommend"):

    with st.spinner("Fetching movies..."):
        names, posters = recommend(selected_movie_name)

    cols = st.columns(5)
    for idx, col in enumerate(cols):
        with col:
            st.text(names[idx])
            st.image(posters[idx])

