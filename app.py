import streamlit as st
import google.generativeai as genai
from moviepy.editor import VideoFileClip
import tempfile
import os
from datetime import datetime

# Configure Gemini
genai.configure(api_key="AIzaSyB92k02wczwkOK3VWuLQZ5JyJWj-uAV6Tk")

def extract_audio(video_path):
    video = VideoFileClip(video_path)
    audio_path = "temp_audio.wav"
    video.audio.write_audiofile(audio_path)
    return audio_path

def transcribe_audio(audio_path):
    # REAL IMPLEMENTATION (requires API key)
    import assemblyai as aai
    aai.settings.api_key = "c612fbf57f4a4d5eafa66cc16aa633c6"

    config = aai.TranscriptionConfig(
        speaker_labels=True,
        speakers_expected=10,
        disfluencies=False
    )
    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(audio_path, config=config)

    if transcript.status == aai.TranscriptStatus.error:
        raise Exception(transcript.error)

    # Format transcript with speaker labels
    formatted_transcript = ""
    for utterance in transcript.utterances:
        formatted_transcript += f"Speaker {utterance.speaker}: {utterance.text}\n"
    return formatted_transcript

def generate_meeting_minutes(transcript):
    model = genai.GenerativeModel("gemini-1.5-pro")
    prompt = f'''Generate professional meeting minutes from the following transcript with these specifications:

# Formatting Requirements:
- Use Markdown formatting
- Begin with "## Meeting Minutes" header
- Include **Date/Time** and **Attendees** sections
- Organize content under "### Key Decisions" and "### Action Items" sections
- For decisions: Use numbered lists with clear ownership
- For action items: Use bullet points with assignees and deadlines
- Highlight postponed items under "### Postponed Discussions"
- Maintain formal business tone
- Keep summary concise but comprehensive

# Content Requirements:
1. Extract and verify meeting date/time from transcript
2. Identify all participants (use "Speaker X" if names unavailable)
3. Focus on concrete decisions and action items
4. Note any tabled discussions with reasons
5. Exclude casual conversation and focus on substantive content

Transcript:
{transcript}'''

    response = model.generate_content(prompt)
    return response.text

# Streamlit UI
st.set_page_config(layout="wide", page_title="AI Meeting Minutes Generator")
st.title("Professional Meeting Minutes Generator")
st.write("Upload a meeting recording to generate formatted minutes")

uploaded_file = st.file_uploader("Choose a video file", type=["mp4", "mov"])

if uploaded_file:
    col1, col2 = st.columns(2)
    with col1:
        st.video(uploaded_file)

    if st.button("Generate Minutes", type="primary"):
        with st.spinner("Processing meeting content..."):
            try:
                # Save video temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                    tmp.write(uploaded_file.getvalue())
                    video_path = tmp.name

                # Process audio
                audio_path = extract_audio(video_path)
                transcript = transcribe_audio(audio_path)
                minutes = generate_meeting_minutes(transcript)

                with col2:
                    st.subheader("Generated Minutes")
                    st.markdown(minutes, unsafe_allow_html=True)

                    # Download button
                    st.download_button(
                        label="Download Minutes",
                        data=minutes,
                        file_name=f"meeting_minutes_{datetime.now().strftime('%Y%m%d')}.md",
                        mime="text/markdown"
                    )

                # Cleanup
                os.unlink(video_path)
                os.unlink(audio_path)

            except Exception as e:
                st.error(f"Processing error: {str(e)}")
                st.info("Please ensure your video contains clear audio and try again.")
