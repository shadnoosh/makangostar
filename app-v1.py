import streamlit as st
import base64
st.set_page_config(page_title="املاک مسکن گستر", layout="wide")

# st.markdown("""
#
#     <style>
#     /* Apply RTL globally */
#     html, body, [class*="css"] {
#         direction: rtl;
#         text-align: right;
#         font-family: Vazirmatn, sans-serif;
#     }
#
#     .login-box {
#         background-color: #ffffff;
#         padding: 2rem;
#         border-radius: 16px;
#         box-shadow: 0 4px 20px rgba(0,0,0,0.1);
#         max-width: 100px;
#         margin: 3rem auto;
#     }
#
#     .login-title {
#         font-size: 1.4rem;
#         font-weight: bold;
#         text-align: center;
#         margin-bottom: 2rem;
#         color: #333;
#     }
#
#     input {
#         border-radius: 10px !important;
#         text-align: right !important;
#     }
#
#     .stTextInput > div > div {
#         direction: rtl;
#     }
#
#     .stButton > button {
#         width: 100%;
#         border-radius: 10px;
#         background-color: #ff4b4b;
#         color: white;
#         font-weight: bold;
#     }
#     </style>
# """, unsafe_allow_html=True)
# Function to inject the local font and updated CSS
def load_local_font_css(font_path, font_name="Isfahan"):
    with open(font_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")

    st.markdown(f"""
        <style>
        @font-face {{
            font-family: '{font_name}';
            src: url(data:font/ttf;base64,{encoded}) format('truetype');
            font-weight: normal;
            font-style: normal;
        }}
        *, html, body, div, span, input, textarea, button {{
            font-family: 'Isfahan', sans-serif !important;
        }}
        html, body, [class*="css"] {{
            direction: rtl;
            text-align: right;
            # font-family: '{font_name}', sans-serif;
            background-color: #f9f9f9;
        }}
        
       
        .login-box {{
            background-color: #ffffff;
            padding: 2rem;
            border-radius: 16px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            max-width: 400px;
            margin: 3rem auto;
        }}

        .login-title {{
            font-size: 3rem;
            font-weight: bold;
            text-align: center;
            margin-bottom: 2rem;
            color: #1a1919;
        }}

        input {{
            border-radius: 10px !important;
            text-align: right !important;
        }}

        .stTextInput > div > div {{
            direction: rtl;
        }}

        .stButton > button {{
            width: 100%;
            border-radius: 10px;
            background-color: #935f9e;
            color: white;
            font-weight: bold;
            height: 3rem;
            font-size: 2rem;
            transition: 0.3s ease;
        }}

        .stButton > button:hover {{
            background-color: #571f63;
            cursor: pointer;
        }}
        </style>
    """, unsafe_allow_html=True)


# Load your local font (adjust path if needed)
load_local_font_css("fonts/Isfahan_YasDL.com.ttf")

import uuid
import pandas as pd
import bcrypt
import os
import plotly.express as px
from urllib.parse import quote
import numpy as np
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import time



# Define file paths
USER_DATA_FILE = "users.csv"
PROPERTY_DATA_FILE = "houses.csv"

# --- Utility Functions ---
# to convert int and floats to number, it gets pandas series, if cant be converted, instead of raising error, it yeilds Nan using "coerce"
def safe_to_numeric(series):
    return pd.to_numeric(series, errors='coerce')

#converting bool values in pandas series to True and Flase
def safe_to_bool(series):
    # Handle various string representations and actual booleans
    bool_map = {"True": True, "False": False, "TRUE": True, "FALSE": False, True: True, False: False, "1": True, "0": False, 1: True, 0: False}
    # Apply mapping, keep others as NaN or original, then attempt bool conversion
    mapped = series.map(bool_map)
    # Fill non-boolean values with False (or choose another default)
    return mapped.fillna(False).astype(bool)

# --- User Data Functions ---
def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        try:
            return pd.read_csv(USER_DATA_FILE)
        except pd.errors.EmptyDataError:
            return pd.DataFrame(columns=["username", "password_hash"])
    else:
        df = pd.DataFrame(columns=["username", "password_hash"])
        df.to_csv(USER_DATA_FILE, index=False)
        return df

def save_user_data(df):
    df.to_csv(USER_DATA_FILE, index=False)

def hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
#compares the entered password with the hashed password , the hash password is passed as stored_hash
def verify_password(stored_hash, provided_password):
    try:
        if isinstance(stored_hash, str) and stored_hash.startswith("b\'"):
            stored_hash = eval(stored_hash)
        elif not isinstance(stored_hash, bytes):
            return False
        return bcrypt.checkpw(provided_password.encode("utf-8"), stored_hash)
    except (ValueError, TypeError):
        return False

# --- Property Data Functions ---
def load_property_data():
    try:
        df = pd.read_csv(PROPERTY_DATA_FILE, encoding='utf-8-sig')
        numeric_cols = ["قیمت به ازای هر متر", "قیمت کل(ريال)", "متراژ زمین", "متراژ بر", "زیر بنا", "عمر (سال ساخت)", "تعداد خواب", "طبقه", "عرض خیابان"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = safe_to_numeric(df[col])

        bool_cols = ["پارکینگ", "انباری", "آسانسور", "حیاط", "زیرزمین"]
        for col in bool_cols:
             if col in df.columns:
                 df[col] = safe_to_bool(df[col])

        address_cols = ["منطقه", "خیابان", "آدرس", "کاربری", "جهت", "نوع سند", "امکانات متفرقه", "نوع متریال کف", "تاسیسات", "مالک اصلی", "تلفن", "موبایل", "توضیحات متفرقه", "وضعیت"]
        for col in address_cols: # Treat more columns as strings
            if col in df.columns:
                df[col] = df[col].astype(str).fillna('')

        # Handle date column specifically if needed
        date_col = "تاريخ ثبت"
        if date_col in df.columns:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce').dt.date

        return df
    except FileNotFoundError:
        st.error(f"Error: Property data file not found at {PROPERTY_DATA_FILE}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading property data: {e}")
        return pd.DataFrame()

def save_property_data(df):
    try:
        # Convert date back to string if necessary for CSV compatibility
        date_col = "تاريخ ثبت"
        if date_col in df.columns and pd.api.types.is_datetime64_any_dtype(df[date_col]):
             df[date_col] = df[date_col].astype(str)
        elif date_col in df.columns and pd.api.types.is_object_dtype(df[date_col]):
             # If it became object (e.g. contains date objects), convert safely
             df[date_col] = pd.to_datetime(df[date_col], errors='coerce').dt.strftime('%Y-%m-%d')

        df.to_csv(PROPERTY_DATA_FILE, index=False, encoding='utf-8-sig')
    except Exception as e:
        st.error(f"Error saving property data: {e}")

# Initialize session state
# st.set_page_config(layout="wide") # Use wide layout
def geocode_address(address):
    geolocator = Nominatim(user_agent="real_estate_app")
    try:
        location = geolocator.geocode("ایران، " + address)
        if location:
            return location.latitude, location.longitude
    except GeocoderTimedOut:
        time.sleep(1)
        return geocode_address(address)
    return None, None
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = None
if "property_data" not in st.session_state:
    st.session_state["property_data"] = load_property_data()

# --- Authentication Pages ---
# def show_login_page():
#     # st.title("صفحه ورود")
#     # st.title("به املاک مسکن گستر خوش آمدید")
#     st.markdown("<h1 style='text-align: center;'>صفحه ورود</h1>", unsafe_allow_html=True)
#     st.markdown("<h2 style='text-align: center;'>به املاک مسکن گستر خوش آمدید</h2>", unsafe_allow_html=True)
#
#     col1, col2, col3 = st.columns([1,2,1])
#     with col2:
#         with st.form("login_form"):
#             username = st.text_input("نام کاربری")
#             password = st.text_input("رمز عبور", type="password")
#             # put the input button at the right side
#             btn_col1, btn_col2, btn_col3 = st.columns([2, 0.2, 0.8])
#             with btn_col3:
#                 submitted = st.form_submit_button("ورود")
#             if submitted:
#                 users_df = load_user_data()
#                 user_record = users_df[users_df["username"] == username]
#                 if not user_record.empty:
#                     stored_hash = user_record.iloc[0]["password_hash"]
#                     if verify_password(stored_hash, password):
#                         st.session_state["logged_in"] = True
#                         st.session_state["username"] = username
#                         st.session_state["property_data"] = load_property_data()
#                         st.success(f"کاربر  {username} خوش آمدید!")
#                         st.rerun()
#                     else:
#                         st.error("نام کاربری یا رمز عبور اشتباه است")
#                 else:
#                     st.error("نام کاربری یا رمز عبور اشتباه است")

def toggle_button(option):
    if st.session_state.active_button == option:
        st.session_state.active_button = None
    else:
        st.session_state.active_button = option
    st.session_state.map_index = None  # reset map on category change


def show_on_google_map(df):
    for idx, row in df.iterrows():
        # Create the full address string
        address_parts = [
            str(row.get("آدرس", "")),
            str(row.get("خیابان", "")),
            str(row.get("منطقه", ""))
        ]
        full_address = "، ".join([part for part in address_parts if part.strip() != ""])

        # Create a container for each row
        with st.container():
            st.markdown(f"**🏠 آدرس {idx + 1}:** {full_address}")

            col1, col2 = st.columns([1, 5])
            with col1:
                if st.button("📍 نمایش روی نقشه", key=f"map_button_{idx}"):
                    st.session_state.map_index = idx
            with col2:
                st.markdown("---")

            # ✅ Show the map only for the selected row
            if st.session_state.map_index == idx:
                maps_query = full_address.replace(" ", "+")
                maps_url = f"https://www.google.com/maps/search/{maps_query}"

                st.markdown(f"[🗺 مشاهده در گوگل مپ]({maps_url})", unsafe_allow_html=True)
                st.components.v1.iframe(
                    f"https://maps.google.com/maps?q={maps_query}&t=&z=15&ie=UTF8&iwloc=&output=embed",
                    height=300,
                    scrolling=False
                )


def show_data_with_map_button(file_path):
    try:
        df = pd.read_excel(file_path)
    except Exception as e:
        st.error(f"خطا در بارگذاری فایل: {e}")

        return

    df.columns = df.columns.str.strip()
    st.write("✅ روی دکمه‌ی 'نمایش روی نقشه' کنار هر آدرس کلیک کنید:")
    st.dataframe(df)

    # Initialize session state if not already set
    if "map_index" not in st.session_state:
        st.session_state.map_index = None
def show_login_page():
    # st.markdown("<h2 class='form-title'>ورود به سامانه املاک مسکن گستر</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Whole form inside styled box
        with st.container():
            # st.markdown('<div class="login-box">', unsafe_allow_html=True)
            st.markdown('<div class="login-title">ورود به سامانه املاک مسکن گستر</div>', unsafe_allow_html=True)
            with st.form("login_form"):
                username = st.text_input("نام کاربری", key="login_username")
                password = st.text_input("رمز عبور", type="password", key="login_password")

                submitted = st.form_submit_button("ورود")

            if submitted:
                users_df = load_user_data()
                user_record = users_df[users_df["username"] == username]
                if not user_record.empty:
                    stored_hash = user_record.iloc[0]["password_hash"]
                    if verify_password(stored_hash, password):
                            st.session_state["logged_in"] = True
                            st.session_state["username"] = username
                            st.session_state["property_data"] = load_property_data()
                            st.success(f"کاربر {username} خوش آمدید!")
                            st.rerun()
                    else:
                            st.error("نام کاربری یا رمز عبور اشتباه است")
                else:
                        st.error("نام کاربری یا رمز عبور اشتباه است")

            # st.markdown("</div>", unsafe_allow_html=True)
def show_register_page():
    # st.title("Real Estate Dashboard - Register")
    # st.markdown("<h1 style='text-align: center;'>صفحه ثبت نام</h1>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center;'>ثبت نام در سامانه املاک مسکن گستر</h2>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        with st.form("register_form"):
            new_username = st.text_input("نام کاربری ")
            new_password = st.text_input("رمز عبور", type="password")
            confirm_password = st.text_input("تکرار رمز عبور", type="password")
            btn_col1, btn_col2, btn_col3 = st.columns([2, 0.2, 0.8])
            with btn_col3:
                submitted = st.form_submit_button("ثبت نام")
            # submitted = st.form_submit_button("ثبت نام")
            if submitted:
                if not new_username or not new_password or not confirm_password:
                    st.warning("Please fill in all fields.")
                    return
                if new_password != confirm_password:
                    st.error("Passwords do not match!")
                    return
                users_df = load_user_data()
                if new_username in users_df["username"].values:
                    st.error("Username already exists. Please choose another one.")
                else:
                    hashed_pw = hash_password(new_password)
                    new_user = pd.DataFrame([[new_username, hashed_pw]], columns=["username", "password_hash"])
                    users_df = pd.concat([users_df, new_user], ignore_index=True)
                    save_user_data(users_df)
                    st.success("Registration successful! You can now log in.")



# --- Main App Logic ---
def main_app():
    st.sidebar.title(f"کاربر {st.session_state['username']} خوش آمدید!")
    if st.sidebar.button("Logout"):
        st.session_state["logged_in"] = False
        st.session_state["username"] = None
        st.session_state["property_data"] = pd.DataFrame()
        st.rerun()

    st.sidebar.title("منوی ورود")
    page = st.sidebar.radio("Go to", ["View Data", "Add Property","Search Property", "Update/Delete Property", "Visualize Data", "Map View"])

    df = st.session_state["property_data"]

    # Define expected columns based on initial file or a standard set
    expected_columns = ["کد", "کد فایل", "تاريخ ثبت", "کاربری", "جهت", "عرض خیابان", "عمر (سال ساخت)", "نوع سند", "متراژ زمین", "متراژ بر", "زیر بنا", "طبقه", "تعداد خواب", "پارکینگ", "انباری", "آسانسور", "حیاط", "زیرزمین", "امکانات متفرقه", "نوع متریال کف", "تاسیسات", "قیمت به ازای هر متر", "قیمت کل(ريال)", "مالک اصلی", "تلفن", "موبایل", "منطقه", "خیابان", "آدرس", "توضیحات متفرقه", "وضعیت", "تصویر", "مسیر تصویر"]
    if df.empty and page != "Add Property":
        st.warning("No property data loaded or file is empty/corrupted. Add data via \'Add Property\' or check the source file.")
        return
    elif df.empty and page == "Add Property":
        # Create an empty DF with expected columns for the Add form
        df = pd.DataFrame(columns=expected_columns)
        # Don't save this back, just use for form structure

    id_column = "کد"
    address_col = "آدرس"
    street_col = "خیابان"
    region_col = "منطقه"

    # Check for essential columns in the actual loaded data (st.session_state["property_data"])
    loaded_df = st.session_state["property_data"]
    essential_cols = [id_column, address_col, street_col, region_col]
    missing_essential = [col for col in essential_cols if col not in loaded_df.columns]
    if missing_essential:
        st.error(f"Essential columns missing from data: {', '.join(missing_essential)}. Some features might be unavailable.")
        if page == "Map View" and (address_col not in loaded_df.columns):
            st.stop()
        if page == "Update/Delete Property" and (id_column not in loaded_df.columns):
             st.stop()

    # Determine usable ID column from loaded data
    usable_id_column = None
    if id_column in loaded_df.columns:
        usable_id_column = id_column
    else:
        potential_ids = [col for col in loaded_df.columns if loaded_df[col].is_unique and not loaded_df[col].isnull().all()]
        if potential_ids:
            usable_id_column = potential_ids[0]
            st.warning(f"Using \'{usable_id_column}\' as unique identifier.")
        else:
             st.error("No suitable unique identifier column found. Update/Delete operations disabled.")
             if page == "Update/Delete Property":
                 st.stop()

    # # --- Page Implementations ---
    # if page == "View Data":
    #     st.header("View Properties")
    #     search_term = st.text_input("Search Properties (any column)")
    #     display_df = loaded_df.copy()
    #     if search_term:
    #         mask = display_df.astype(str).apply(lambda x: x.str.contains(search_term, case=False, na=False)).any(axis=1)
    #         display_df = display_df[mask]
    #     st.dataframe(display_df)

    if page == "View Data":
        st.header("👁️ مشاهده املاک")

        tab1, tab2, tab3 = st.tabs(["مسکونی", "تجاری", "صنعتی"])

        # ✅ Session state initialization
        if "active_button" not in st.session_state:
            st.session_state.active_button = None
        if "map_index" not in st.session_state:
            st.session_state.map_index = None



        options = {
            "آپارتمان": "آپارتمان.xlsx",
            "باغ و ویلا": "باغ و ویلا.xlsx",
            "زمین": "زمین.xlsx",
            "خانه ویلایی": "خانه ویلایی.xlsx"
        }

        with tab1:
            st.subheader("🏠 نوع ملک را انتخاب کنید:")

            active = st.session_state.active_button
            if active:
                st.button(active, on_click=toggle_button, args=(active,))
                show_data_with_map_button(options[active])
                st.divider()
                for opt in options:
                    if opt != active:
                        st.button(opt, on_click=toggle_button, args=(opt,), key=f"bottom_{opt}")
            else:
                for opt in options:
                    st.button(opt, on_click=toggle_button, args=(opt,), key=f"top_{opt}")

        with tab2:
            st.info("داده‌های تجاری در دسترس نیستند.")
        with tab3:
            st.info("داده‌های صنعتی در دسترس نیستند.")


    #
    elif page == "Add Property":
        st.header("Add New Property")

        main_tabs = st.tabs(["مسکونی", "تجاری", "صنعتی"])

        # Define field structures for مسکونی tabs
        moskoni_structure = {
            "آپارتمان": ["قیمت به ازای هر متر", "قیمت کل(ريال)", "متراژ زمین", "متراژ بر", "کد فایل", "زیر بنا",
                         "عمر (سال ساخت)", "خیابان", "تعداد خواب", "طبقه", "عرض خیابان", "کد", "کاربری", "جهت",
                         "نوع سند",
                         "امکانات متفرقه", "نوع متریال کف", "تاسیسات", "مالک اصلی", "تلفن", "موبایل", "منطقه",
                         "آدرس", "توضیحات متفرقه", "تصویر", "مسیر تصویر", "وضعیت", "تاريخ ثبت", "پارکینگ",
                         "انباری", "آسانسور", "حیاط", "زیرزمین"],
            "باغ و ویلا": ["قیمت کل(ريال)", "متراژ زمین", "زیر بنا", "عمر (سال ساخت)", "خیابان", "کد", "تاريخ ثبت",
                           "حیاط", "زیرزمین", "استخر", "سند"],
            "زمین": ["قیمت به ازای هر متر", "قیمت کل(ريال)", "متراژ زمین", "عرض زمین", "خیابان", "کد", "تاريخ ثبت",
                     "سند"],
            "خانه ویلایی": ["قیمت کل(ريال)", "متراژ زمین", "زیر بنا", "عمر (سال ساخت)", "تعداد خواب", "طبقه",
                            "عرض خیابان", "کد", "تاريخ ثبت", "پارکینگ", "انباری", "حیاط", "زیرزمین"]
        }

        with main_tabs[0]:  # Only handling مسکونی for now
            moskoni_tabs = st.tabs(list(moskoni_structure.keys()))

            for idx, tab_name in enumerate(moskoni_structure.keys()):
                with moskoni_tabs[idx]:
                    st.subheader(f"فرم افزودن - {tab_name}")

                    columns = moskoni_structure[tab_name]

                    with st.form(f"form_{tab_name}", clear_on_submit=True):
                        new_data = {}
                        form_cols = st.columns(3)
                        col_widgets = {}

                        for i, col in enumerate(columns):

                            current_col_widget = form_cols[i % 3]

                            if col == "تصویر":
                                col_widgets[col] = current_col_widget.file_uploader(
                                    label=col,
                                    type=["jpg", "jpeg", "png"]
                                )
                            elif col in ["قیمت به ازای هر متر", "قیمت کل(ريال)", "متراژ زمین", "متراژ بر", "زیر بنا",
                                       "عرض زمین"]:
                                col_widgets[col] = current_col_widget.number_input(col, value=0.0, format="%f")
                            elif col in ["عمر (سال ساخت)", "خیابان", "تعداد خواب", "طبقه", "عرض خیابان", "کد",
                                         "کد فایل"]:
                                col_widgets[col] = current_col_widget.number_input(col, value=0, format="%d")
                            elif col == "تاريخ ثبت":
                                col_widgets[col] = current_col_widget.date_input(col)
                            elif col in ["پارکینگ", "انباری", "آسانسور", "حیاط", "زیرزمین", "استخر"]:
                                col_widgets[col] = current_col_widget.checkbox(col)
                            else:
                                col_widgets[col] = current_col_widget.text_input(col)
                            i += 1
                        submitted = st.form_submit_button("افزودن ملک")

                        if submitted:
                            for col, widget in col_widgets.items():
                                new_data[col] = widget

                            try:
                                # Convert values
                                converted_data = {}
                                image_file = None

                                for col in columns:
                                    value = new_data.get(col)

                                    if col == "تصویر":
                                        image_file = value
                                        if image_file is not None:
                                            # Save image
                                            save_folder = os.path.join("images", tab_name)
                                            os.makedirs(save_folder, exist_ok=True)

                                            # Create unique filename
                                            image_filename = f"{uuid.uuid4().hex}_{image_file.name}"
                                            image_path = os.path.join(save_folder, image_filename)

                                            # Save image file
                                            with open(image_path, "wb") as f:
                                                f.write(image_file.read())

                                            # Add image info to data
                                            converted_data["نام فایل تصویر"] = image_filename
                                            converted_data["آدرس تصویر"] = image_path
                                        else:
                                            converted_data["نام فایل تصویر"] = ""
                                            converted_data["آدرس تصویر"] = ""
                                    elif col in ["قیمت به ازای هر متر", "قیمت کل(ريال)", "متراژ زمین", "متراژ بر",
                                                 "زیر بنا", "عرض زمین"]:
                                        converted_data[col] = float(value) if value is not None else np.nan
                                    elif col in ["عمر (سال ساخت)", "خیابان", "تعداد خواب", "طبقه", "عرض خیابان", "کد",
                                                 "کد فایل"]:
                                        converted_data[col] = int(value) if value is not None else np.nan
                                    elif col == "تاريخ ثبت":
                                        converted_data[col] = pd.to_datetime(
                                            value).date() if value is not None else None
                                    elif col in ["پارکینگ", "انباری", "آسانسور", "حیاط", "زیرزمین", "استخر"]:
                                        converted_data[col] = bool(value)
                                    else:
                                        converted_data[col] = str(value) if value is not None else ''

                                # Save to Excel
                                df_path = f"{tab_name}.xlsx"
                                try:
                                    existing_df = pd.read_excel(df_path)
                                except FileNotFoundError:
                                    existing_df = pd.DataFrame(columns=columns + ["نام فایل تصویر", "آدرس تصویر"])

                                new_df = pd.DataFrame([converted_data])
                                new_df = new_df.reindex(columns=existing_df.columns)
                                final_df = pd.concat([existing_df, new_df], ignore_index=True)

                                final_df.to_excel(df_path, index=False)
                                st.success(f"ملک جدید به '{tab_name}' با موفقیت افزوده شد.")
                                st.rerun()

                            except Exception as e:
                                st.error(f"خطا در افزودن ملک: {e}")
    elif page == "Search Property":

        moskoni_structure = {
            "آپارتمان": ["قیمت کل(ريال)", "متراژ زمین", "خیابان", "تعداد خواب"],
            "باغ و ویلا": ["قیمت کل(ريال)", "متراژ زمین", "خیابان"],
            "زمین": ["قیمت کل(ريال)", "متراژ زمین", "عرض زمین", "خیابان"],
            "خانه ویلایی": ["قیمت کل(ريال)", "متراژ زمین", "خیابان", "تعداد خواب"]
        }

        st.title("🔍 جستجو املاک")

        main_tabs = st.tabs(["مسکونی", "تجاری", "صنعتی"])

        # Only مسکونی implemented for now
        with main_tabs[0]:
            st.subheader("جستجو در املاک مسکونی")

            category = st.selectbox("نوع ملک", list(moskoni_structure.keys()))
            search_fields = moskoni_structure[category]

            # Define input widgets dynamically
            user_filters = {}
            cols = st.columns(2)
            for i, field in enumerate(search_fields):

                with cols[i % 2]:
                    if "قیمت" in field or "متراژ" in field or "عرض" in field or "تعداد خواب" in field:
                        min_val = st.number_input(f"{field} حداقل", min_value=0, value=0, step=1)
                        max_val = st.number_input(f"{field} حداکثر", min_value=0, value=0, step=1)
                        user_filters[field] = (min_val, max_val)
                    else:
                        user_filters[field] = st.text_input(f"{field} (شامل)")

            search_btn = st.button("جستجو")

            if search_btn:
                file_path = f"{category}.xlsx"
                try:
                    df = pd.read_excel(file_path, dtype=str)
                    df["عمر (سال ساخت)"] = df["عمر (سال ساخت)"].astype(str)
                    for field, value in user_filters.items():
                        if isinstance(value, tuple):  # Numeric range
                            min_v, max_v = value
                            if max_v > 0:
                                df[field] = pd.to_numeric(df[field], errors='coerce')
                                df = df[(df[field] >= min_v) & (df[field] <= max_v)]
                        else:  # Text match
                            if value.strip():
                                df = df[df[field].astype(str).str.contains(value, na=False)]

                    st.success(f"{len(df)} نتیجه یافت شد.")
                    st.dataframe(df)

                    # Map Section
                    if "خیابان" in df.columns and "آدرس" in df.columns:
                        df["آدرس کامل"] = "خیابان"+" "+df["خیابان"].fillna('') +","+ " " + df["آدرس"].fillna('')

                        st.write("آدرس‌ها:")
                        st.dataframe(df[["آدرس کامل"]])  # show addresses as usual

                        st.write("لینک‌ موقعیتهای پیدا شده روی گوگل مپ:")
                        for addr in df["آدرس کامل"]:
                            url = f"https://www.google.com/maps/search/?api=1&query={addr.replace(' ', '+')}"
                            # display clickable link in markdown
                            st.markdown(f"[📍 مشاهده در نقشه]({url})")

                    else:
                            st.warning("هیچ آدرسی قابل موقعیت‌یابی نبود.")
                except FileNotFoundError:
                    st.error("فایل مربوطه پیدا نشد. ابتدا فایل‌هایی مانند آپارتمان.xlsx را ایجاد نمایید.")

    elif page == "Update/Delete Property":
        display_df = loaded_df.copy()
        st.header("Update or Delete Property")
        if not usable_id_column:
             st.error("Cannot perform Update/Delete without a unique identifier column.")
             return

        st.info("Edit data directly in the table. Changes are saved automatically. To delete rows, use the built-in delete option in the editor.")
        column_config = {usable_id_column: st.column_config.NumberColumn(disabled=True)}
        for col in loaded_df.columns:
            if pd.api.types.is_bool_dtype(loaded_df[col].dtype):
                column_config[col] = st.column_config.CheckboxColumn(default=False)
            elif pd.api.types.is_datetime64_any_dtype(loaded_df[col].dtype) or (isinstance(loaded_df[col].dtype, pd.ArrowDtype) and pa.types.is_date(loaded_df[col].dtype.pyarrow_dtype)):
                 column_config[col] = st.column_config.DateColumn(format="YYYY-MM-DD")

        edited_df = st.data_editor(
            loaded_df,
            key="data_editor",
            num_rows="dynamic",
            use_container_width=True,
            column_config=column_config,
            hide_index=True,
            disabled=[usable_id_column] # Disable editing for the ID column
        )

        if not edited_df.equals(loaded_df):
             # Add validation if needed (e.g., check for duplicate IDs if they were editable)
             st.session_state["property_data"] = edited_df
             save_property_data(st.session_state["property_data"])
             st.success("Changes saved!")
             # st.rerun() # Might cause issues with data_editor state, often not needed.

    elif page == "Visualize Data":
        st.header("Data Visualization")
        viz_df = loaded_df.copy()
        if viz_df.empty:
            st.warning("No data available for visualization.")
            return

        st.subheader("Property Price Distribution")
        price_col = "قیمت کل(ريال)"
        if price_col in viz_df.columns and pd.api.types.is_numeric_dtype(viz_df[price_col]):
            fig_hist = px.histogram(viz_df.dropna(subset=[price_col]), x=price_col, title="Distribution of Total Property Prices", labels={price_col: "Total Price (Rial)"})
            st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.warning(f"Column au3000{price_col}\u3001 not found or not numeric for histogram.")

        st.subheader("property location")
        region = "منطقه"
        if region in viz_df.columns and pd.api.types.is_numeric_dtype(viz_df[region]):
            fig_hist = px.histogram(viz_df.dropna(subset=[region]), x=region,
                                    title="Distribution of region",
                                    labels={region: "region"})
            st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.warning(f"Column au3000{region}\u3001 not found or not numeric for histogram.")

        st.subheader("Properties per Region")
        if region_col in viz_df.columns:
            region_counts = viz_df[region_col].astype(str).fillna('Unknown').value_counts().reset_index()
            region_counts.columns = [region_col,'count']
            fig_bar = px.bar(region_counts, x=region_col, y='count', title="Number of Properties by Region", labels={region_col: "Region", 'count': "Number of Properties"})
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.warning(f"Column au3000{region_col}\u3001 not found for bar chart.")

        st.subheader("Property Type Distribution")
        type_col = "کاربری"
        if type_col in viz_df.columns:
            type_counts = viz_df[type_col].astype(str).fillna('Unknown').value_counts().reset_index()
            type_counts.columns = [type_col, 'count']
            fig_pie = px.pie(type_counts, names=type_col, values='count', title="Distribution of Property Types", labels={type_col: "Property Type", 'count': "Count"})
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.warning(f"Column au3000{type_col}\u3001 not found for pie chart.")

        st.subheader("Property Age vs. Price")
        age_col = "عمر (سال ساخت)"
        if price_col in viz_df.columns and age_col in viz_df.columns and pd.api.types.is_numeric_dtype(viz_df[price_col]) and pd.api.types.is_numeric_dtype(viz_df[age_col]):
            scatter_df = viz_df.dropna(subset=[age_col, price_col])
            fig_scatter = px.scatter(scatter_df, x=age_col, y=price_col, title="Property Age vs. Total Price",
                                     labels={age_col: "Age (Years)", price_col: "Total Price (Rial)"},
                                     hover_data=[usable_id_column] if usable_id_column else None)
            st.plotly_chart(fig_scatter, use_container_width=True)
        else:
            st.warning(f"Columns au3000{age_col}\u3001 or au3000{price_col}\u3001 not found or not numeric for scatter plot.")
        st.subheader("Property Price per Square Meter vs. Total Price")
        price_per_meter_col = "قیمت به ازای هر متر"
        if price_col in viz_df.columns and price_per_meter_col in viz_df.columns and pd.api.types.is_numeric_dtype(viz_df[price_col]) and pd.api.types.is_numeric_dtype(viz_df[price_per_meter_col]):
            scatter_df = viz_df.dropna(subset=[price_per_meter_col, price_col])
            fig_scatter = px.scatter(scatter_df, x=price_per_meter_col, y=price_col, title="Price per Square Meter vs. Total Price",
                                     labels={price_per_meter_col: "Price per Square Meter (Rial)", price_col: "Total Price (Rial)"},
                                     hover_data=[usable_id_column] if usable_id_column else None)
            st.plotly_chart(fig_scatter, use_container_width=True)
        else:
            st.warning(f"Columns au3000{price_per_meter_col}\u3001 or au3000{price_col}\u3001 not found or not numeric for scatter plot.")


        st.subheader("💰 میانگین قیمت کل در هر منطقه (Price vs. Region)")

        region_col = "منطقه"
        price_col = "قیمت کل(ريال)"

        # بررسی وجود ستون‌ها و نوع عددی بودن قیمت
        if region_col in viz_df.columns and price_col in viz_df.columns and pd.api.types.is_numeric_dtype(
                viz_df[price_col]):
            region_price_df = viz_df.dropna(subset=[region_col, price_col])

            # محاسبه میانگین قیمت در هر منطقه
            avg_price_per_region = region_price_df.groupby(region_col)[price_col].mean().reset_index()

            fig_bar = px.bar(
                avg_price_per_region,
                x=region_col,
                y=price_col,
                title="میانگین قیمت کل در هر منطقه (Average Total Price by Region)",
                labels={region_col: "منطقه", price_col: "میانگین قیمت کل"},
                text_auto=True
            )

            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.warning(f"ستون‌های '{region_col}' یا '{price_col}' یافت نشدند یا قیمت عددی نیست.")
    elif page == "Map View":
        st.header("Map View")
        map_df = loaded_df.copy()
        if map_df.empty:
            st.warning("No properties to display on map.")
            return

        st.info("Click on the link next to an address to view it on Google Maps.")
        if address_col not in map_df.columns:
            st.warning(f"Address column (au3000{address_col}\u3001) not found. Cannot generate map links.")
            return

        def create_full_address(row):
            parts = [row.get(address_col, ''), row.get(street_col, ''), row.get(region_col, '')]
            return ','.join(filter(None, [str(p).strip() for p in parts])).strip()

        map_df['full_address'] = map_df.apply(create_full_address, axis=1)
        map_df_filtered = map_df[map_df['full_address'] != ''].copy()

        if map_df_filtered.empty:
            st.warning("No properties with valid address information found.")
            return

        for index, row in map_df_filtered.iterrows():
            address = row['full_address']
            map_query = quote(address)
            map_url = f"https://www.google.com/maps/search/?api=1&query={map_query}"
            display_id = f"ID: {row[usable_id_column]} - " if usable_id_column and usable_id_column in row and pd.notna(row[usable_id_column]) else ""
            st.markdown(f"{display_id}{address} [🗺️ View on Map]({map_url})", unsafe_allow_html=True)
            st.divider()

# --- Page Routing ---
if not st.session_state["logged_in"]:
    #shows the logo of maskangostar
    st.sidebar.image("assets/logo.png", width=300)
    choice = st.sidebar.radio("انتخاب", ["ورود", "ثبت نام"])
    if choice == "ورود":
        show_login_page()
    elif choice == "ثبت نام":
        show_register_page()
else:
    # Import pyarrow here only when needed and logged in, as it's used by st.data_editor implicitly sometimes
    try:
        import pyarrow as pa
    except ImportError:
        st.warning("PyArrow not installed, some data editor features might be limited.")
        pa = None # Set to None if import fails
    main_app()

