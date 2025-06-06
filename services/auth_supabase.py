import streamlit as st
import jwt

def handle_google_auth():
    """
    Gère l'authentification Google via Supabase et stocke les infos dans st.session_state
    """
    if "email" in st.session_state and "user_id" in st.session_state:
        return {"email": st.session_state["email"], "id": st.session_state["user_id"]}

    access_token = st.query_params.get("access_token", None)
    if isinstance(access_token, list):
        access_token = access_token[0]

    if access_token and access_token.count('.') == 2:
        try:
            decoded = jwt.decode(access_token, options={"verify_signature": False})
            email = decoded.get("email")
            user_id = decoded.get("sub")  # auth.uid() est dans "sub"
            if email and user_id:
                st.session_state["access_token"] = access_token
                st.session_state["email"] = email
                st.session_state["user_id"] = user_id
                st.query_params.clear()
                st.rerun()
        except Exception as e:
            st.warning(f"Erreur JWT : {e}")

    if "email" in st.session_state and "user_id" in st.session_state:
        return {"email": st.session_state["email"], "id": st.session_state["user_id"]}

    return None

def get_login_url(supabase_url: str, redirect_url: str):
    from urllib.parse import quote
    return f"{supabase_url}/auth/v1/authorize?provider=google&redirect_to={quote(redirect_url)}"
