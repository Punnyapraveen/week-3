import streamlit as st
import google.generativeai as genai
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
import time

# Configuration - Replace with your actual Gemini API key
GEMINI_API_KEY = "AIzaSyCp3OhyjXeoHg644fm6_O0ZZ2uf_RtGT1E"

# Path to chromedriver executable
CHROMEDRIVER_PATH = r"C:\Users\DELL\.wdm\drivers\chromedriver\win64\124.0.6367.207\chromedriver-win32/chromedriver.exe"

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--headless")  # Headless for Streamlit server environments
    service = Service(CHROMEDRIVER_PATH)
    return webdriver.Chrome(service=service, options=options)

def fetch_web_content(url):
    driver = setup_driver()
    try:
        driver.get(url)
        content = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        ).text
        return content[:10000]
    except Exception as e:
        return f"❌ Error fetching content: {str(e)}"
    finally:
        driver.quit()

def summarize_with_gemini(text):
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(f"Summarize this in 3-5 bullet points: {text}")
        return response.text
    except Exception as e:
        return f"❌ Gemini error: {str(e)}"

def summarize_topic(topic):
    url = f"https://en.wikipedia.org/wiki/{topic.replace(' ', '_')}"
    content = fetch_web_content(url)
    if content.startswith("❌"):
        return content, url
    summary = summarize_with_gemini(content)
    return summary, url

# Streamlit UI
st.set_page_config(page_title="Web Research Assistant", layout="centered")
st.title("🌍 Web Research Assistant")
st.write("Enter a topic below and get a summarized research output from Wikipedia using Gemini AI.")

topic = st.text_input("🔍 Enter a topic:", "")

if st.button("Summarize"):
    if not topic.strip():
        st.warning("Please enter a valid topic.")
    else:
        with st.spinner("Fetching and summarizing content..."):
            summary, url = summarize_topic(topic.strip())
        st.success("✅ Summary Generated!")
        st.markdown(f"### Summary for **{topic}**")
        st.markdown(summary)
        st.markdown(f"📚 [Source: Wikipedia]({url})")
