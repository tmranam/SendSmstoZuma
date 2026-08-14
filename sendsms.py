import streamlit as st
import pandas as pd

# Set page configuration to wide layout
st.set_page_config(layout="wide")

st.title("📊 Dynamic SMS Marketing Dashboard")

# Initialize session state for tracking selected rows across redraws
if "selected_rows" not in st.session_state:
    st.session_state.selected_rows = set()

# -----------------------------------------------------------------------------
# STEP 1: GLOBAL SMS TEMPLATE CONFIGURATION
# -----------------------------------------------------------------------------
st.markdown("### ✉️ Step 1: Draft Your SMS Template")
st.caption(
    "Type your message below. Use the buttons to instantly inject dynamic "
    "placeholders that change for every person."
)

# Text area for the base SMS message
sms_text = st.text_area(
    "SMS Message Template",
    value="Dear {Name}, for your {Description}, your budget is {Budget} and we collected {Collection}.",
    height=120,
    key="sms_template_input",
)

# Helper UI buttons to show users what variables they can use
col_btn1, col_btn2, col_btn3, col_btn4, col_btn5 = st.columns(5)
with col_btn1:
    st.info("**{Name}**")
with col_btn2:
    st.info("**{Description}** (Majlis)")
with col_btn3:
    st.info("**{Budget}**")
with col_btn4:
    st.info("**{Collection}**")
with col_btn5:
    st.info("**{Difference}**")


# -----------------------------------------------------------------------------
# STEP 2: FILE UPLOAD
# -----------------------------------------------------------------------------
st.markdown("---")
st.markdown("### 📂 Step 2: Upload Recipient List")
uploaded_file = st.file_uploader(
    "Upload a CSV or Excel file containing columns: Name, Description, Budget, Collection, Difference",
    type=["csv", "xlsx"],
)

if uploaded_file is not None:
    # Read the file based on its extension
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"Error reading file: {e}")
        st.stop()

    # Clean column names to strip any accidental whitespace
    df.columns = [col.strip() for col in df.columns]

    # Required column validation
    required_cols = ["Name", "Description", "Budget", "Collection", "Difference"]
    missing_cols = [col for col in required_cols if col not in df.columns]

    if missing_cols:
        st.error(f"Your file is missing required columns: {', '.join(missing_cols)}")
        st.stop()

    # Ensure financial metrics are numbers for calculation safety
    df["Budget"] = pd.to_numeric(df["Budget"], errors="coerce").fillna(0.0)
    df["Collection"] = pd.to_numeric(df["Collection"], errors="coerce").fillna(0.0)
    df["Difference"] = pd.to_numeric(df["Difference"], errors="coerce").fillna(0.0)

    # -------------------------------------------------------------------------
    # STEP 3: INTERACTIVE DASHBOARD GRID WITH CHECKBOXES
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 👥 Step 3: Select Recipients and Preview Messages")

    # Use Streamlit's built-in data editor with checkbox capability
    # This automatically adds a selection column on the left side
    edited_df = st.data_editor(
        df,
        column_config={
            "Name": st.column_config.TextColumn("Recipient Name", width="medium"),
            "Description": st.column_config.TextColumn(
                "Description / Majlis", width="medium"
            ),
            "Budget": st.column_config.NumberColumn("Budget ($)", format="$%.2f"),
            "Collection": st.column_config.NumberColumn(
                "Collection ($)", format="$%.2f"
            ),
            "Difference": st.column_config.NumberColumn(
                "Difference ($)", format="$%.2f"
            ),
        },
        disabled=required_cols,  # Keep the original data locked/read-only
        num_rows="fixed",
        use_container_width=True,
        hide_index=True,
        key="data_grid",
    )

    # Extract which rows were selected via the data_editor UI
    # Note: Streamlit data_editor returns row state details under `st.session_state`
    grid_state = st.session_state.get("data_grid", {})
    selected_indices = []
    if "edited_rows" in grid_state:
        # Check if rows are flagged or interacted with
        # For a standard row selection workflow, we look at rows where the user clicked
        pass

    # Alternative bulletproof check using a dedicated Select column if grid selection is preferred
    # To guarantee clean row selection on the left, we inject a 'Select' boolean column dynamically
    df_with_select = df.copy()
    df_with_select.insert(0, "Select", False)

    # Re-render with explicit checkbox column on the left
    final_edited_df = st.data_editor(
        df_with_select,
        column_config={
            "Select": st.column_config.CheckboxColumn(
                "Select", default=False, width="small"
            ),
            "Budget": st.column_config.NumberColumn(format="$%.2f"),
            "Collection": st.column_config.NumberColumn(format="$%.2f"),
            "Difference": st.column_config.NumberColumn(format="$%.2f"),
        },
        disabled=required_cols,
        num_rows="fixed",
        use_container_width=True,
        hide_index=True,
        key="main_table",
    )

    # Filter out only rows where the user checked the "Select" box
    selected_rows = final_edited_df[final_edited_df["Select"] == True]

    # -------------------------------------------------------------------------
    # STEP 4: SMS GENERATION AND ACTION
    # -------------------------------------------------------------------------
    st.markdown("### 🚀 Generated SMS Previews")

    if not selected_rows.empty:
        st.success(f"Selected {len(selected_rows)} recipient(s).")

        # Create an asset block to show exactly what will be sent
        messages_to_send = []

        for idx, row in selected_rows.iterrows():
            # Handle percentage formatting logic dynamically if needed
            pct_collected = (
                (row["Collection"] / row["Budget"] * 100)
                if row["Budget"] > 0
                else 0.0
            )

            # Safeguard text formatting replacement to avoid KeyError crashes
            try:
                individual_sms = sms_text.format(
                    Name=row["Name"],
                    Description=row["Description"],
                    Budget=f"${row['Budget']:,.2f}",
                    Collection=f"${row['Collection']:,.2f}",
                    Difference=f"${row['Difference']:,.2f}",
                    Percentage=f"{pct_collected:.1f}%",
                )
            except KeyError as e:
                st.error(
                    f"Invalid placeholder used in text box: {e}. Please use only the valid brackets listed above."
                )
                st.stop()

            messages_to_send.append(
                {"Name": row["Name"], "Final SMS Text": individual_sms}
            )

        # Display the custom generated text previews to the user
        preview_df = pd.DataFrame(messages_to_send)
        st.table(preview_df)

        # Trigger send event
        if st.button("📤 Send SMS to Selected", type="primary"):
            # Placeholder for your SMS Gateway integration (e.g., Twilio, Vonage, Sinch)
            with st.spinner("Processing text messages..."):
                for msg in messages_to_send:
                    # Logic code to route text messages via API goes here
                    pass
            st.toast("🎉 Messages simulated/sent successfully!", icon="✅")

    else:
        st.warning("⚠️ Check the box next to a name on the table to generate their SMS.")

else:
    st.info("💡 Please upload a CSV or Excel data file above to populate the system.")
