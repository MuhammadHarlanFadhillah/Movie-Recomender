import streamlit as st
import joblib
import pandas as pd
import requests

# ==========================================
# 1. KONFIGURASI HALAMAN
# ==========================================
st.set_page_config(layout="wide", page_title="CineMatch AI")

# 🔑 API KEY (Jangan Lupa Isi!)
API_KEY = "ISI API KEY MU DISINI" 

# CSS Custom untuk mempercantik font rating
st.markdown("""
<style>
    .rating-font {
        font-size:20px !important;
        font-weight: bold;
        color: #f1c40f;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. FUNGSI API & DATA
# ==========================================
def fetch_movie_details(movie_id):
    try:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US"
        data = requests.get(url).json()
        
        poster_path = data.get('poster_path')
        if poster_path:
            full_path = "https://image.tmdb.org/t/p/w500" + poster_path
        else:
            full_path = "https://via.placeholder.com/500x750?text=No+Poster"
            
        overview = data.get('overview', 'Tidak ada sinopsis.')
        rating = data.get('vote_average', 0)
        genres = [g['name'] for g in data.get('genres', [])]
        date = data.get('release_date', '-')
        
        return full_path, overview, rating, genres, date
    except:
        return "https://via.placeholder.com/500x750?text=Error", "Error", 0, [], "-"

@st.cache_data
def load_data():
    movies_df = joblib.load('models/movie_list.pkl')
    similarity = joblib.load('models/similarity.pkl')
    return movies_df, similarity

movies, similarity = load_data()

# ==========================================
# 3. HEADER & PENCARIAN
# ==========================================
st.title("🍿 CineMatch: AI Movie Recommender")

movie_list = movies['title'].values
selected_movie = st.selectbox(
    "🎬 Pilih film favoritmu untuk melihat detail & rekomendasi:",
    movie_list
)

# ==========================================
# 4. LOGIKA UTAMA
# ==========================================
if st.button('🔍 Tampilkan Detail & Rekomendasi', key='search_btn'):
    
    # --- A. BAGIAN HERO (SOROTAN UTAMA) ---
    # Kita cari data film yang DIPILIH user dulu
    try:
        # Ambil data film terpilih dari database lokal
        idx_selected = movies[movies['title'] == selected_movie].index[0]
        id_selected = movies.iloc[idx_selected].movie_id
        
        # Ambil detail lengkap dari API TMDB
        poster, overview, rating, genres, date = fetch_movie_details(id_selected)
        
        st.markdown("---")
        st.subheader("🎥 Film Pilihanmu")
        
        # Bikin Layout 2 Kolom (Kiri: Poster, Kanan: Teks Sinopsis)
        col_hero1, col_hero2 = st.columns([1, 3]) # Kolom kanan lebih lebar
        
        with col_hero1:
            st.image(poster, use_container_width=True)
        
        with col_hero2:
            st.markdown(f"## **{selected_movie}** ({date[:4]})")
            st.markdown(f"**Genre:** {', '.join(genres)}")
            st.markdown(f'<p class="rating-font">⭐ Rating: {rating:.1f}/10</p>', unsafe_allow_html=True)
            st.markdown("### 📖 Sinopsis")
            st.write(overview)

        # --- B. BAGIAN REKOMENDASI (BAWAH) ---
        st.markdown("---")
        st.subheader(f"Karena kamu suka '{selected_movie}', coba tonton ini juga:")
        st.markdown("###") # Spacer
        
        # Hitung Kemiripan (Logic AI)
        distances = similarity[idx_selected]
        recommendations = sorted(list(enumerate(distances)), reverse=True, key=lambda x:x[1])[1:6]
        
        # Tampilkan 5 Rekomendasi Berjejer
        cols = st.columns(5)
        for idx, col in enumerate(cols):
            rec_movie_id = movies.iloc[recommendations[idx][0]].movie_id
            rec_title = movies.iloc[recommendations[idx][0]].title
            
            # Panggil API untuk rekomendasi
            rec_poster, rec_overview, rec_rating, rec_genres, rec_date = fetch_movie_details(rec_movie_id)
            
            with col:
                st.image(rec_poster, use_container_width=True)
                st.markdown(f"**{rec_title}**")
                st.caption(f"⭐ {rec_rating:.1f}")
                
                # Tombol detail kecil
                with st.expander("Lihat Plot"):
                    st.write(rec_overview)

    except Exception as e:
        st.error(f"Error: {e}. Cek API Key.")