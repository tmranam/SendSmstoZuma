import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("📊 Dynamic SMS Marketing Dashboard")

# -----------------------------------------------------------------------------
# STEP 1: GLOBAL SMS TEMPLATE CONFIGURATION
# -----------------------------------------------------------------------------
st.markdown("### ✉️ Step 1: Draft Your SMS Template")
st.caption("Use brackets like `{Name}` or `{Description}` to insert row details dynamically.")

sms_text = st.text_area(
    "SMS Message Template",
    value="Dear {Name}, for your {Description}, your budget is {Budget} and we collected {Collection}.",
    height=120,
    key="sms_template_input",
)

# Helper visual guide
col_btn1, col_btn2, col_btn3, col_btn4, col_btn5, col_btn6 = st.columns(6)
col_btn1.info("**{Name}**")
col_btn2.info("**{Description}**")
col_btn3.info("**{Budget}**")
col_btn4.info("**{Collection}**")
col_btn5.info("**{Difference}**")
col_btn6.info("**{Percentage}**")

# -----------------------------------------------------------------------------
# STEP 2: FILE UPLOAD
# -----------------------------------------------------------------------------
st.markdown("---")
st.markdown("### 📂 Step 2: Upload Recipient List")
uploaded_file = st.file_uploader("Upload a CSV or Excel file", type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"Error reading file: {e}")
        st.stop()

    df.columns = [col.strip() for col in df.columns]
    required_cols = ["Name", "Description", "Budget", "Collection", "Difference"]
    missing_cols = [col for col in required_cols if col not in df.columns]

    if missing_cols:
        st.error(f"Missing required columns: {', '.join(missing_cols)}")
        st.stop()

    # Clean data numbers
    for col in ["Budget", "Collection", "Difference"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    # -------------------------------------------------------------------------
    # STEP 3: INTERACTIVE DASHBOARD GRID WITH CHECKBOXES
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 👥 Step 3: Select Recipients and Preview Messages")

    df_with_select = df.copy()
    df_with_select.insert(0, "Select", False)

    final_edited_df = st.data_editor(
        df_with_select,
        column_config={
            "Select": st.column_config.CheckboxColumn("Select", default=False, width="small"),
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

    selected_rows = final_edited_df[final_edited_df["Select"] == True]

    # -------------------------------------------------------------------------
    # STEP 4: SMS GENERATION
    # -------------------------------------------------------------------------
    st.markdown("### 🚀 Generated SMS Previews")

    if not selected_rows.empty:
        st.success(f"Selected {len(selected_rows)} recipient(s).")
        messages_to_send = []

        for idx, row in selected_rows.iterrows():
            pct_collected = (row["Collection"] / row["Budget"] * 100) if row["Budget"] > 0 else 0.0
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
                st.error(f"Invalid placeholder used: {e}")
                st.stop()

            messages_to_send.append({"Name": row["Name"], "Final SMS Text": individual_sms})

        st.table(pd.DataFrame(messages_to_send))

        if st.button("📤 Send SMS to Selected", type="primary"):
            st.toast("🎉 Messages successfully processed!", icon="✅")
    else:
        st.warning("⚠️ Check the box next to a name to generate their SMS.")
else:
    st.info("💡 Please upload a CSV or Excel file to begin.")
