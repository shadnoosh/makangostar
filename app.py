import streamlit as st
st.set_page_config(page_title="املاک مسکن گستر", layout="wide")

import pandas as pd
import bcrypt
import os
import plotly.express as px
from urllib.parse import quote
import numpy as np





# Apply global styling
st.markdown("""
    <style>
        body {
            direction: rtl;
        }
        .main {
            font-family: IRANSans, sans-serif;
        }
        .stTextInput>div>div>input,
        .stTextArea>div>textarea,
        .stNumberInput>div>div input {
            direction: rtl;
            text-align: right;
        }
        .stSelectbox>div>div>div>div {
            direction: rtl;
            text-align: right;
        }
        .stButton>button {
            background-color: #4A00E0;
            background-image: linear-gradient(to right, #4A00E0, #8E2DE2);
            color: white;
            font-weight: bold;
            border-radius: 0.5rem;
        }
        .form-container {
            background-color: #fff;
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            margin-top: 2rem;
        }
        .form-title {
            text-align: center;
            color: #4A00E0;
        }
        .login-logo {
            text-align: center;
            margin-bottom: 2rem;
        }
    </style>
""", unsafe_allow_html=True)

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
def show_login_page():
    st.markdown("<h2 class='form-title'>ورود به سامانه املاک مسکن گستر</h2>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container():
            st.markdown(
                """
                <style>
                    .stForm {
                        background-color: #ffffff;
                        padding: 2rem;
                        border-radius: 12px;
                        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
                        margin-top: 1rem;
                        margin-bottom: 2rem;
                    }
                </style>
                """,
                unsafe_allow_html=True
            )
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
def show_register_page():
    # st.title("Real Estate Dashboard - Register")
    st.markdown("<h2 style='text-align: center;'>خوش آمدید</h2>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center;'>برای ثبت نام درسامانه املاک مسکن گستر، مشخصات خود را وارد کنید</h4>", unsafe_allow_html=True)

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
    st.sidebar.title(f"Welcome, {st.session_state['username']}!")
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
        st.header("🔍 جستجو و مشاهده املاک")

        # پیش‌پردازش ستون‌ها
        loaded_df.columns = loaded_df.columns.str.strip()
        display_df = loaded_df.copy()

        # فیلتر بر اساس فیلدهای خاص
        col1, col2 = st.columns(2)

        with col1:
            bedrooms = st.text_input("تعداد خواب (مثلاً: 2)")
            street = st.text_input("خیابان")
            region = st.text_input("منطقه")
            price_meter_min = st.number_input("قیمت هر متر (حداقل)", value=0)
            price_meter_max = st.number_input("قیمت هر متر (حداکثر)", value=100000000)

        with col2:
            land_min = st.number_input("متراژ زمین (حداقل)", value=0)
            land_max = st.number_input("متراژ زمین (حداکثر)", value=10000)
            total_price_min = st.number_input("قیمت کل (حداقل)", value=0)
            total_price_max = st.number_input("قیمت کل (حداکثر)", value=10000000000)

        # فیلترهای متنی
        if "تعداد خواب" in display_df.columns and bedrooms:
            display_df = display_df[display_df["تعداد خواب"].astype(str).str.contains(bedrooms, na=False)]

        if "خیابان" in display_df.columns and street:
            display_df = display_df[display_df["خیابان"].astype(str).str.contains(street, na=False)]

        if "منطقه" in display_df.columns and region:
            display_df = display_df[display_df["منطقه"].astype(str).str.contains(region, na=False)]

        # فیلترهای بازه‌ای عددی
        if "متراژ زمین" in display_df.columns:
            display_df["متراژ زمین"] = pd.to_numeric(display_df["متراژ زمین"], errors="coerce")
            display_df = display_df[(display_df["متراژ زمین"] >= land_min) & (display_df["متراژ زمین"] <= land_max)]

        if "قیمت هر متر" in display_df.columns:
            display_df["قیمت هر متر"] = pd.to_numeric(display_df["قیمت هر متر"], errors="coerce")
            display_df = display_df[
                (display_df["قیمت هر متر"] >= price_meter_min) & (display_df["قیمت هر متر"] <= price_meter_max)]

        if "قیمت کل" in display_df.columns:
            display_df["قیمت کل"] = pd.to_numeric(display_df["قیمت کل"], errors="coerce")
            display_df = display_df[
                (display_df["قیمت کل"] >= total_price_min) & (display_df["قیمت کل"] <= total_price_max)]

        # فیلتر کلی
        search_term = st.text_input("جستجوی کلی در همه ستون‌ها")
        if search_term:
            mask = display_df.astype(str).apply(lambda x: x.str.contains(search_term, case=False, na=False)).any(axis=1)
            display_df = display_df[mask]


        st.subheader("📍 نمایش ملک/ املاک یافته شده روی نقشه گوگل")

        # فقط اگر آدرس داریم
        st.dataframe(display_df)

        if not display_df.empty:
            for idx, row in display_df.iterrows():
                st.markdown(f"### 🏠 ملک شماره {idx + 1}")

                address_parts = [
                    str(row.get("آدرس", "")),
                    str(row.get("خیابان", "")),
                    str(row.get("منطقه", ""))
                ]
                full_address = "، ".join([part for part in address_parts if part.strip() != ""])
                maps_query = full_address.replace(" ", "+")
                maps_url = f"https://www.google.com/maps/search/{maps_query}"

                st.markdown(f"[📍 مشاهده در گوگل مپ]({maps_url})", unsafe_allow_html=True)
                st.components.v1.iframe(
                    f"https://maps.google.com/maps?q={maps_query}&t=&z=15&ie=UTF8&iwloc=&output=embed",
                    height=300,
                    scrolling=False
                )
                st.markdown("---")
        else:
            st.warning("هیچ ملکی با مشخصات وارد شده یافت نشد.")
    elif page == "Add Property":
        st.header("Add New Property")
        # Use columns from the potentially empty df created for structure
        cols_to_add = df.columns
        with st.form("add_property_form", clear_on_submit=True):
            new_data = {}
            form_cols = st.columns(3)
            col_widgets = {}
            i = 0
            for col in cols_to_add:
                current_col_widget = form_cols[i % 3]
                try:
                    # Get dtype from loaded_df if available, else default
                    col_type = loaded_df[col].dtype if col in loaded_df.columns else None
                except KeyError:
                    col_type = None

                # Determine input type based on column name conventions or expected types
                if col in ["قیمت به ازای هر متر", "قیمت کل(ريال)", "متراژ زمین", "متراژ بر", "زیر بنا"]:
                    col_widgets[col] = current_col_widget.number_input(f"{col}", value=0.0, format="%f")
                elif col in ["عمر (سال ساخت)","خیابان", "تعداد خواب", "طبقه", "عرض خیابان", "کد", "کد فایل"]: # Assuming these are integers
                    col_widgets[col] = current_col_widget.number_input(f"{col}", value=0, format="%d", step=1)
                elif col == "تاريخ ثبت":
                    col_widgets[col] = current_col_widget.date_input(f"{col}", value=None)
                elif col in ["پارکینگ", "انباری", "آسانسور", "حیاط", "زیرزمین"]:
                    col_widgets[col] = current_col_widget.checkbox(f"{col}")
                else: # Default to string
                    col_widgets[col] = current_col_widget.text_input(f"{col}")
                i += 1

            submitted = st.form_submit_button("Add Property")
            if submitted:
                try:
                    # Retrieve values from widgets
                    for col, widget in col_widgets.items():
                        new_data[col] = widget

                    # Basic Validation & Type Conversion
                    valid = True
                    converted_data = {}
                    for col in cols_to_add:
                        value = new_data.get(col)
                        try:
                            if col in ["قیمت به ازای هر متر", "قیمت کل(ريال)", "متراژ زمین", "متراژ بر", "زیر بنا"]:
                                converted_data[col] = float(value) if value is not None else np.nan
                            elif col in ["عمر (سال ساخت)","خیابان", "تعداد خواب", "طبقه", "عرض خیابان", "کد", "کد فایل"]:
                                converted_data[col] = int(value) if value is not None else np.nan
                            elif col == "تاريخ ثبت":
                                converted_data[col] = pd.to_datetime(value).date() if value is not None else None
                            elif col in ["پارکینگ", "انباری", "آسانسور", "حیاط", "زیرزمین"]:
                                converted_data[col] = bool(value)
                            else:
                                converted_data[col] = str(value) if value is not None else ''
                        except (ValueError, TypeError) as e:
                            st.error(f"Invalid input for column au3000{col}\u3001: {value}. Error: {e}")
                            valid = False
                            break # Stop processing on first error

                    if valid:
                        # Check unique ID constraint
                        if usable_id_column and usable_id_column in converted_data and not loaded_df.empty and converted_data[usable_id_column] in loaded_df[usable_id_column].values:
                            st.error(f"Error: ID {converted_data[usable_id_column]} already exists.")
                        else:
                            new_df_row = pd.DataFrame([converted_data])
                            new_df_row = new_df_row.reindex(columns=loaded_df.columns if not loaded_df.empty else expected_columns)

                            st.session_state["property_data"] = pd.concat([loaded_df, new_df_row], ignore_index=True)
                            save_property_data(st.session_state["property_data"])
                            st.success("Property added successfully!")
                            st.rerun()
                except Exception as e:
                    st.error(f"Error adding property: {e}")
    elif page == "Search Property":

        st.subheader("Search Properties")

        df = st.session_state["property_data"]
        df.columns = df.columns.str.strip()  # clean up column names
        # st.write("Columns in data:", df.columns.tolist())
        if df.empty:
            st.info("No data available to search.")
        else:
            with st.expander("Filter Options"):
                col1, col2 = st.columns(2)

                bedrooms = col1.selectbox("تعداد خواب", options=["همه"] + sorted(df["تعداد خواب"].dropna().unique().tolist()))
                area_min = col2.number_input("حداقل متراژ زمین", min_value=0, value=10)
                area_max = col2.number_input("حداکثر متراژ زمین", min_value=0, value=1000)

                street = col1.text_input("خیابان")
                region = col2.text_input("منطقه")

                price_per_meter_min = col1.number_input("حداقل قیمت هر متر", min_value=0, value=1000000)
                price_per_meter_max = col1.number_input("حداکثر قیمت هر متر", min_value=0, value=1000000000)

                total_price_min = col2.number_input("حداقل قیمت کل", min_value=0, value=1000000000)
                total_price_max = col2.number_input("حداکثر قیمت کل", min_value=0, value=1000000000000)

            filtered_df = df.copy()

            if bedrooms != "همه":
                filtered_df = filtered_df[filtered_df["تعداد خواب"] == bedrooms]
                filtered_df = filtered_df[
                (filtered_df["متراژ زمین"].astype(float) >= area_min) &
                (filtered_df["متراژ زمین"].astype(float) <= area_max) &
                (filtered_df["قیمت به ازای هر متر"].astype(float) >= price_per_meter_min) &
                (filtered_df["قیمت به ازای هر متر"].astype(float) <= price_per_meter_max) &
                (filtered_df["قیمت کل(ريال)"].astype(float) >= total_price_min) &
                (filtered_df["قیمت کل(ريال)"].astype(float) <= total_price_max)
                ]

            if street:
                filtered_df = filtered_df[filtered_df["خیابان"].str.contains(street, na=False)]

            if region:
                filtered_df = filtered_df[filtered_df["منطقه"].str.contains(region, na=False)]

            st.write(f"نتایج جستجو: {len(filtered_df)} مورد یافت شد.")
            st.dataframe(filtered_df.reset_index(drop=True))

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
    st.sidebar.image("https://streamlit.io/images/brand/streamlit-logo-secondary-colormark-darktext.svg", width=200)
    choice = st.sidebar.radio("انتخاب", ["Login", "Register"])
    if choice == "Login":
        show_login_page()
    elif choice == "Register":
        show_register_page()
else:
    # Import pyarrow here only when needed and logged in, as it's used by st.data_editor implicitly sometimes
    try:
        import pyarrow as pa
    except ImportError:
        st.warning("PyArrow not installed, some data editor features might be limited.")
        pa = None # Set to None if import fails
    main_app()

