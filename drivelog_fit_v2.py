import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# Function to connect to SQLite database
def get_connection():
    return sqlite3.connect('drivelog_fit.db')

def create_table():
    with get_connection() as conn:
        conn.execute('''
        CREATE TABLE IF NOT EXISTS drive_data (
            id INTEGER PRIMARY KEY,
            date DATE NOT NULL,
            driver TEXT NOT NULL,
            passenger TEXT NOT NULL,
            destination TEXT NOT NULL,
            alcohol TEXT NOT NULL,
            start_time TEXT NOT NULL,
            back_time TEXT NOT NULL,
            start_km INTEGER NOT NULL,
            back_km INTEGER NOT NULL,
            dist_km INTEGER NOT NULL,
            highway TEXT NOT NULL,
            checkup TEXT NOT NULL,
            error TEXT NOT NULL,
            gas TEXT NOT NULL
        )
        ''')

create_table()

# Function to format time as string
def format_time_str(time_obj):
    return f"{time_obj.hour:02d}:{time_obj.minute:02d}:{time_obj.second:02d}"

# Collect user inputs
st.header('Fit 運行管理記録')
date = st.date_input('日付を選択してください')
driver = st.text_input('運転者名を入力してください')
passenger = st.text_input('同乗者名を入力してください')
destination = st.text_input('訪問先を入力してください')
alcohol = st.selectbox('アルコールチェックの有無を選択してください', ('◎', '✕'))
start_time = st.time_input('出発時間を選択してください') 
back_time = st.time_input('帰社時間を選択してください')
start_km = st.number_input('出発時距離を入力してください') 
back_km = st.number_input('帰社時距離を入力してください') 
dist_km = st.number_input('今回走行距離を入力してください')  
highway = st.selectbox('高速使用の有無を選択してください', ('あり', 'なし'))
checkup = st.selectbox('点検結果を選択してください', ('異常あり', '異常無し'))
error = st.text_input('異常内容を入力してください')
gas = st.selectbox('残燃料を選択してください', ('満タン', '3/4', '1/2', '1/4'))

# Convert time objects to strings
start_time_str = format_time_str(start_time)  
back_time_str = format_time_str(back_time)    

# Save data to SQLite
if st.button('保存'):
    try:
        with get_connection() as conn:
            conn.execute('''
                INSERT INTO drive_data (date, driver, passenger, destination, alcohol, start_time, back_time, start_km, back_km, dist_km, highway, checkup, error, gas) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (date, driver, passenger, destination, alcohol, start_time_str, back_time_str, start_km, back_km, dist_km, highway, checkup, error, gas))
        st.success('データが保存されました')
    except sqlite3.Error as e:
        st.error(f'データを保存中にエラーが発生しました: {e}')

# Display data and allow deletion and editing
try:
    with get_connection() as conn:
        df = pd.read_sql_query("SELECT * FROM drive_data", conn)

    if not df.empty:
        df['delete'] = False
        df['edit'] = False

        delete_flags = []
        edit_flags = []
        for i in range(len(df)):
            delete_flags.append(st.checkbox(f"削除 {df.at[i, 'id']}", key=f"delete_{df.at[i, 'id']}"))
            edit_flags.append(st.checkbox(f"編集 {df.at[i, 'id']}", key=f"edit_{df.at[i, 'id']}"))

        df['delete'] = delete_flags
        df['edit'] = edit_flags

        st.dataframe(df.drop(columns=['delete', 'edit']))

        # Delete selected rows
        if st.button('選択した行を削除'):
            to_delete_ids = df[df['delete']].id.tolist()
            if to_delete_ids:
                with get_connection() as conn:
                    conn.executemany("DELETE FROM drive_data WHERE id = ?", [(id,) for id in to_delete_ids])
                st.success(f'{len(to_delete_ids)} 行が削除されました')
                st.experimental_rerun()

        # Edit selected row
        edit_ids = df[df['edit']].id.tolist()
        if len(edit_ids) == 1:
            edit_id = edit_ids[0]
            with get_connection() as conn:
                row = conn.execute("SELECT * FROM drive_data WHERE id = ?", (edit_id,)).fetchone()
                if row:
                    st.subheader(f'ID: {edit_id} のデータを編集')
                    date = st.date_input('日付を選択してください', value=datetime.strptime(row[1], '%Y-%m-%d'), key='edit_date')
                    driver = st.text_input('運転者名を入力してください', value=row[2], key='edit_driver')
                    passenger = st.text_input('同乗者名を入力してください', value=row[3], key='edit_passenger')
                    destination = st.text_input('訪問先を入力してください', value=row[4], key='edit_destination')
                    alcohol = st.selectbox('アルコールチェックの有無を選択してください', ('◎', '✕'), index=('◎', '✕').index(row[5]), key='edit_alcohol')
                    start_time = st.time_input('出発時間を選択してください', value=datetime.strptime(row[6], '%H:%M:%S').time(), key='edit_start_time')
                    back_time = st.time_input('帰社時間を選択してください', value=datetime.strptime(row[7], '%H:%M:%S').time(), key='edit_back_time')
                    start_km = st.number_input('出発時距離を入力してください', value=row[8], key='edit_start_km')
                    back_km = st.number_input('帰社時距離を入力してください', value=row[9], key='edit_back_km')
                    dist_km = st.number_input('今回走行距離を入力してください', value=row[10], key='edit_dist_km')
                    highway = st.selectbox('高速使用の有無を選択してください', ('あり', 'なし'), index=('あり', 'なし').index(row[11]), key='edit_highway')
                    checkup = st.selectbox('点検結果を選択してください', ('異常あり', '異常無し'), index=('異常あり', '異常無し').index(row[12]), key='edit_checkup')
                    error = st.text_input('異常内容を入力してください', value=row[13], key='edit_error')
                    gas = st.selectbox('残燃料を選択してください', ('満タン', '3/4', '1/2', '1/4'), index=('満タン', '3/4', '1/2', '1/4').index(row[14]), key='edit_gas')

                    if st.button('更新'):
                        try:
                            with get_connection() as conn:
                                conn.execute('''
                                    UPDATE drive_data SET
                                        date = ?,
                                        driver = ?,
                                        passenger = ?,
                                        destination = ?,
                                        alcohol = ?,
                                        start_time = ?,
                                        back_time = ?,
                                        start_km = ?,
                                        back_km = ?,
                                        dist_km = ?,
                                        highway = ?,
                                        checkup = ?,
                                        error = ?,
                                        gas = ?
                                    WHERE id = ?
                                ''', (date, driver, passenger, destination, alcohol, format_time_str(start_time), format_time_str(back_time), start_km, back_km, dist_km, highway, checkup, error, gas, edit_id))
                            st.success('データが更新されました')
                            st.experimental_rerun()
                        except sqlite3.Error as e:
                            st.error(f'データを更新中にエラーが発生しました: {e}')
        elif len(edit_ids) > 1:
            st.error('一度に編集できる行は1つだけです')

except sqlite3.Error as e:
    st.error(f'データの表示中にエラーが発生しました: {e}')


