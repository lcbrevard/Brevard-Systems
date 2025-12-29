#!/usr/bin/env python3
"""Initialize the database from the Excel spreadsheet."""

import sqlite3
import pandas as pd
import os

DATABASE = 'assets.db'
EXCEL_FILE = 'Brevad_Computers.xlsx'

def init_db():
    # Remove existing database
    if os.path.exists(DATABASE):
        os.remove(DATABASE)

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Create assets table
    cursor.execute('''
        CREATE TABLE assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            status TEXT,
            rank REAL,
            net_name TEXT,
            form_factor TEXT,
            vendor TEXT,
            model TEXT,
            screen1 TEXT,
            h_px1 REAL,
            v_px1 REAL,
            screen2 TEXT,
            h_px2 REAL,
            v_px2 REAL,
            cpu TEXT,
            cores_threads TEXT,
            ram TEXT,
            disk1 TEXT,
            disk2 TEXT,
            disk3 TEXT,
            disk4 TEXT,
            ext_disk TEXT,
            location TEXT,
            room TEXT,
            os TEXT,
            os_release TEXT,
            oclp TEXT
        )
    ''')

    # Create notes table
    cursor.execute('''
        CREATE TABLE notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            net_name TEXT,
            note TEXT
        )
    ''')

    # Read Excel file
    df = pd.read_excel(EXCEL_FILE)

    # Column mapping from Excel to database
    excel_to_db = {
        'up?': 'status',
        'rank': 'rank',
        'Net Name': 'net_name',
        'Form\nFactor': 'form_factor',
        'Vendor': 'vendor',
        'Model': 'model',
        'Screen 1': 'screen1',
        'H PX': 'h_px1',
        'V PX': 'v_px1',
        'Screen 2': 'screen2',
        'H PX.1': 'h_px2',
        'V PX.1': 'v_px2',
        'CPU': 'cpu',
        'Cores x \nThreads': 'cores_threads',
        'RAM': 'ram',
        'DISK1': 'disk1',
        'DISK2': 'disk2',
        'DISK3': 'disk3',
        'DISK4': 'disk4',
        'EXT DSK 1': 'ext_disk',
        'Location': 'location',
        'Room': 'room',
        'OS': 'os',
        'Release': 'os_release',
        'OCLP': 'oclp'
    }

    # Find the notes section (rows starting with "Notes" label)
    notes_start = None
    for idx, row in df.iterrows():
        if str(row.iloc[0]).strip() == 'Notes':
            notes_start = idx
            break

    # Import asset data (rows before notes section, excluding empty rows)
    asset_rows = df.iloc[:notes_start] if notes_start else df

    for idx, row in asset_rows.iterrows():
        # Skip empty rows
        if pd.isna(row.iloc[2]) or str(row.iloc[2]).strip() == '':
            continue

        values = []
        for excel_col, db_col in excel_to_db.items():
            if excel_col in df.columns:
                val = row[excel_col]
                if pd.isna(val):
                    val = ''
                elif isinstance(val, float) and val == int(val):
                    val = int(val)
                values.append(str(val) if val != '' else '')
            else:
                values.append('')

        placeholders = ', '.join(['?' for _ in values])
        columns = ', '.join(excel_to_db.values())
        cursor.execute(f'INSERT INTO assets ({columns}) VALUES ({placeholders})', values)

    # Import notes from the Notes section
    # The notes section format: Column 2 has either dates or net_names, Column 3 has note text
    if notes_start is not None:
        notes_df = df.iloc[notes_start + 1:]  # Skip the "Notes" header row
        current_date = None

        for idx, row in notes_df.iterrows():
            col2 = row.iloc[2]
            col3 = row.iloc[3] if len(row) > 3 else None

            # Skip empty rows
            if pd.isna(col2) and pd.isna(col3):
                continue

            col2_str = str(col2).strip() if pd.notna(col2) else ''
            col3_str = str(col3).strip() if pd.notna(col3) else ''

            # Check if col2 is a date (contains Timestamp or looks like YYYY-MM-DD)
            is_date = False
            if pd.notna(col2):
                if hasattr(col2, 'strftime'):  # It's a datetime object
                    current_date = col2.strftime('%Y-%m-%d')
                    is_date = True
                elif len(col2_str) >= 10 and col2_str[4] == '-' and col2_str[7] == '-':
                    current_date = col2_str[:10]
                    is_date = True

            if is_date:
                # This row sets a new date, and may have a note in col3
                if col3_str:
                    cursor.execute('INSERT INTO notes (date, net_name, note) VALUES (?, ?, ?)',
                                 (current_date, '', col3_str))
            elif current_date and col2_str and 'nan' not in col2_str.lower():
                # This is a note row: col2 = net_name (or empty), col3 = note text
                if col3_str:
                    cursor.execute('INSERT INTO notes (date, net_name, note) VALUES (?, ?, ?)',
                                 (current_date, col2_str, col3_str))
                else:
                    # col2 is the note text itself
                    cursor.execute('INSERT INTO notes (date, net_name, note) VALUES (?, ?, ?)',
                                 (current_date, '', col2_str))

    conn.commit()
    conn.close()
    print(f"Database initialized: {DATABASE}")
    print(f"Assets imported from: {EXCEL_FILE}")

if __name__ == '__main__':
    init_db()
