import streamlit as st
import requests

# ------------------ CONFIG ------------------
BACKEND_URL = "http://127.0.0.1:8000/upload-video/"

st.set_page_config(
    page_title="3D Model Simulation",
    page_icon="▣",
    layout="wide"
)

# ------------------ SESSION STATE INIT ------------------
if "sent_to_preprocessing" not in st.session_state:
    st.session_state.sent_to_preprocessing = False

if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

if "preprocess_result" not in st.session_state:
    st.session_state.preprocess_result = None


def reset_state():
    st.session_state.sent_to_preprocessing = False
    st.session_state.preprocess_result = None
    st.session_state.uploader_key += 1
    st.rerun()


# ------------------ GLOBAL CSS ------------------
st.markdown("""
<style>
html, body, [class*="css"] {
    font-family: "Inter", "Segoe UI", sans-serif;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #020617, #020617);
}

/* ================= BIG BUTTONS ================= */
div[data-testid="stButton"] button {
    width: 100%;
    height: 72px !important;
    padding: 0 32px !important;
    font-size: 20px !important;
    font-weight: 700 !important;
    border-radius: 18px !important;
    border: 1px solid rgba(255,255,255,0.3) !important;
    background: linear-gradient(135deg, #1f2937, #111827) !important;
    color: #e5e7eb !important;
}

/* Upload container */
.upload-box {
    background: rgba(17,24,39,0.75);
    border-radius: 18px;
    padding: 2.2rem;
    border: 1px solid rgba(255,255,255,0.08);
}

/* Upload title */
.upload-title {
    font-size: 26px;
    font-weight: 800;
    margin-bottom: 0.8rem;
}

/* Upload success */
.upload-success {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    color: #22c55e;
    font-size: 18px;
    font-weight: 600;
}

/* Info bar */
div[data-testid="stInfo"] {
    padding: 1.4rem;
    font-size: 16px;
    border-radius: 16px;
}

/* Hide filename row */
div[data-testid="stFileUploaderFile"],
section[data-testid="stFileUploader"] ul {
    display: none !important;
}

/* ================= PROCESSING DETAILS ================= */
.detail-card {
    background: rgba(17,24,39,0.65);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 18px;
    padding: 2rem;
    margin-bottom: 1.6rem;
    text-align: center;
}

.metric-big {
    font-size: 48px;
    font-weight: 800;
    color: #e5e7eb;
}

.metric-green {
    font-size: 48px;
    font-weight: 800;
    color: #22c55e;
}
</style>
""", unsafe_allow_html=True)

# ------------------ SIDEBAR ------------------
st.sidebar.title("⚙ Simulation Controls")
st.sidebar.caption("Configure preprocessing mode")
st.sidebar.button("Run Simulation")

# ------------------ MAIN UI ------------------
st.title("▣ 3D Model Simulation")
st.caption("Transforming motion into structure")

# ------------------ UPLOAD SECTION ------------------
st.markdown('<div class="upload-box">', unsafe_allow_html=True)

col_upload, col_status = st.columns([1.2, 2], vertical_alignment="center")

with col_upload:
    st.markdown('<div class="upload-title">⬆ Upload Video</div>', unsafe_allow_html=True)
    uploaded_video = st.file_uploader(
        "",
        type=["mp4", "mov", "avi", "mkv"],
        label_visibility="collapsed",
        key=f"uploaded_video_{st.session_state.uploader_key}"
    )

with col_status:
    if uploaded_video:
        st.markdown('<div class="upload-success">⬤ Video uploaded successfully</div>', unsafe_allow_html=True)
    else:
        st.caption("Select a video file to begin")

st.markdown('</div>', unsafe_allow_html=True)

# ------------------ UPLOAD STATUS ------------------
if uploaded_video:
    st.markdown("### ⬤ Upload Status")

    status_col, action_col = st.columns([3, 1], vertical_alignment="center")

    with status_col:
        if st.session_state.sent_to_preprocessing:
            st.success("Video successfully queued for preprocessing")
        else:
            st.info("Your video has been received and is ready for preprocessing.")

    with action_col:
        if not st.session_state.sent_to_preprocessing:
            if st.button("▶ Send to Preprocessing"):
                with st.spinner("Sending video to preprocessing pipeline..."):
                    files = {
                        "file": (
                            uploaded_video.name,
                            uploaded_video.getvalue(),
                            uploaded_video.type
                        )
                    }
                    response = requests.post(BACKEND_URL, files=files)

                if response.status_code == 200:
                    st.session_state.sent_to_preprocessing = True
                    st.session_state.preprocess_result = response.json()
                    st.rerun()
                else:
                    st.error("Failed to send video to preprocessing")

# ------------------ PROCESSING DETAILS ------------------
if st.session_state.sent_to_preprocessing and st.session_state.preprocess_result:
    data = st.session_state.preprocess_result

    st.markdown("##  Processing Details")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**🖼 Frames Extracted**")
        st.markdown(
            f"""
            <div class="detail-card">
                <div class="metric-big">
                    {data.get("frames_extracted","—")}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown("**⏱ Duration (sec)**")
        st.markdown(
            f"""
            <div class="detail-card">
                <div class="metric-green">
                    {round(data.get("duration_sec",0),2)}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("")
    st.button("⬜ Start new configuration", on_click=reset_state)

# ------------------ FOOTER ------------------
st.markdown("---")
st.caption("▣ 3D Simulation Engine")
