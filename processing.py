import gspread
from gspread_dataframe import get_as_dataframe
import pandas as pd
import openai
import json
import time
from apikey import OPENAI_API_KEY

# --- AUTH ---
openai.api_key = OPENAI_API_KEY
gc = gspread.service_account(filename='creds.json')
sheet = gc.open("UT 402 Final")
worksheet = sheet.sheet1

processed_hashes = set()

# --- HELPERS ---
def load_sheet_data():
    df = get_as_dataframe(worksheet)
    df.dropna(how='all', inplace=True)
    return df

def ensure_output_columns(df):
    for col in ['place', 'keywords', 'urgency', 'department']:
        if col not in df.columns:
            df[col] = pd.NA
    return df

def create_prompt(message):
    return f"""
You are an assistant helping city officials classify incident reports submitted by the public.

Please extract the following information from the incident message below:

1. The most prominent place name within the message
2. The most prominent 1 or 2 keywords that best represent the incident the message is describing
3. The urgency with which the event should be responded to on a scale of 1-10
4. The City Department that is best suited to respond to the incident. Choose between Police, Fire Department, Sanitation, Public Works, and Social Services. If there is not a clear department that you think should respond, or you do not think the event is inordinary enough such that it would require a department to respond to it, just return an empty string.

Message: "{message}"

Respond in JSON format:
{{
  "place": [...],
  "keywords": [...],
  "urgency": "...",
  "department": "..."
}}
"""

def analyze_message_with_gpt(message):
    prompt = create_prompt(message)
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"API Error: {e}")
        return None

def parse_response(response_str):
    try:
        return json.loads(response_str)
    except Exception as e:
        print(f"Parse error: {e}")
        return {"place": [], "keywords": [], "urgency": None, "department": None}

#def update_new_rows(df):
    mask = df[['place', 'keywords', 'urgency', 'department']].isna().any(axis=1)
    for idx, row in df[df[mask].isna()].iterrows():
        raw = analyze_message_with_gpt(row['Message'])
        if raw:
            parsed = parse_response(raw)
            df.at[idx, 'place'] = parsed.get('place')
            df.at[idx, 'keywords'] = parsed.get('keywords')
            df.at[idx, 'urgency'] = parsed.get('urgency')
            df.at[idx, 'department'] = parsed.get('department')
    return df

# def update_new_rows(df):
    for idx, row in df[df['department'].isna()].iterrows():
        raw = analyze_message_with_gpt(row['Message'])  # use lowercase if you normalized columns
        if raw:
            parsed = parse_response(raw)

            # Convert list values to comma-separated strings
            place_val = ', '.join(parsed.get('place')) if isinstance(parsed.get('place'), list) else parsed.get('place')
            keywords_val = ', '.join(parsed.get('keywords')) if isinstance(parsed.get('keywords'), list) else parsed.get('keywords')

            df.at[idx, 'place'] = place_val
            df.at[idx, 'keywords'] = keywords_val
            df.at[idx, 'urgency'] = parsed.get('urgency')
            df.at[idx, 'department'] = parsed.get('department')

    return df

def update_new_rows(df):
    global processed_hashes
    for idx, row in df[df['department'].isna()].iterrows():
        hash_val = row.get('Hash Value')  # adjust to your actual column name
        if not hash_val or hash_val in processed_hashes:
            continue  # Skip if already processed

        raw = analyze_message_with_gpt(row['Message'])
        if raw:
            parsed = parse_response(raw)

            # Format lists
            place_val = ', '.join(parsed.get('place')) if isinstance(parsed.get('place'), list) else parsed.get('place')
            keywords_val = ', '.join(parsed.get('keywords')) if isinstance(parsed.get('keywords'), list) else parsed.get('keywords')

            df.at[idx, 'place'] = place_val
            df.at[idx, 'keywords'] = keywords_val
            df.at[idx, 'urgency'] = parsed.get('urgency')
            df.at[idx, 'department'] = parsed.get('department')

            processed_hashes.add(hash_val)  # mark this row as processed

    return df

# def save_to_sheet(df):
    # df_clean = df.fillna("")
    # worksheet.update([df_clean.columns.values.tolist()] + df_clean.values.tolist())

#def save_to_sheet(df):
    df_clean = df.fillna("")

    # Read current sheet header
    current_data = get_as_dataframe(worksheet)
    current_data.dropna(how='all', inplace=True)

    # Ensure original columns are preserved
    for col in ['place', 'keywords', 'urgency', 'department']:
        if col not in current_data.columns:
            current_data[col] = pd.NA

    # Merge updated NLP values into original sheet
    for idx, row in df.iterrows():
        for col in ['place', 'keywords', 'urgency', 'department']:
            current_data.at[idx, col] = row[col]

    # Update the sheet (no clearing!)
    current_data = current_data.fillna("")
    worksheet.update([current_data.columns.values.tolist()] + current_data.values.tolist())

def save_to_sheet(df):
    df_clean = df.copy()

    # Convert lists (like 'keywords', 'place') to comma-separated strings
    for col in ['place', 'keywords']:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].apply(lambda x: ', '.join(x) if isinstance(x, list) else x)

    df_clean = df_clean.fillna("")

    # Get current sheet content
    current_data = get_as_dataframe(worksheet)
    current_data.dropna(how='all', inplace=True)

    # Add missing columns if needed
    for col in ['place', 'keywords', 'urgency', 'department']:
        if col not in current_data.columns:
            current_data[col] = pd.NA

    # Merge the new NLP values in
    for idx, row in df.iterrows():
        for col in ['place', 'keywords', 'urgency', 'department']:
            current_data.at[idx, col] = row[col]

    # Flatten lists again in case any were added
    for col in ['place', 'keywords']:
        if col in current_data.columns:
            current_data[col] = current_data[col].apply(lambda x: ', '.join(x) if isinstance(x, list) else x)

    # Final cleanup before update
    current_data = current_data.fillna("")
    worksheet.update([current_data.columns.values.tolist()] + current_data.values.tolist())


# --- RUN ONCE OR SCHEDULE ---
while True:
    df = load_sheet_data()
    df = ensure_output_columns(df)
    df = update_new_rows(df)
    save_to_sheet(df)
    time.sleep(20)