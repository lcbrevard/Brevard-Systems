from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
import os

app = Flask(__name__)
app.jinja_env.globals.update(zip=zip)
DATABASE = 'assets.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def get_columns():
    return [
        'id', 'status', 'rank', 'net_name', 'form_factor', 'vendor', 'model',
        'screen1', 'h_px1', 'v_px1', 'screen2', 'h_px2', 'v_px2',
        'cpu', 'cores_threads', 'ram', 'disk1', 'disk2', 'disk3', 'disk4',
        'ext_disk', 'location', 'room', 'os', 'os_release', 'oclp'
    ]

def get_display_columns():
    return [
        'ID', 'Status', 'Rank', 'Net Name', 'Form Factor', 'Vendor', 'Model',
        'Screen 1', 'H PX', 'V PX', 'Screen 2', 'H PX', 'V PX',
        'CPU', 'Cores x Threads', 'RAM', 'DISK1', 'DISK2', 'DISK3', 'DISK4',
        'EXT DSK 1', 'Location', 'Room', 'OS', 'Release', 'OCLP'
    ]

@app.route('/')
def index():
    return redirect(url_for('table_view'))

@app.route('/table')
def table_view():
    conn = get_db()
    assets = conn.execute('SELECT * FROM assets ORDER BY rank').fetchall()
    conn.close()
    columns = get_columns()
    display_columns = get_display_columns()
    return render_template('table.html', assets=assets, columns=columns, display_columns=display_columns)

@app.route('/form')
@app.route('/form/<int:asset_id>')
def form_view(asset_id=None):
    conn = get_db()
    assets = conn.execute('SELECT id, net_name FROM assets ORDER BY rank').fetchall()

    if asset_id is None and assets:
        asset_id = assets[0]['id']

    asset = None
    if asset_id:
        asset = conn.execute('SELECT * FROM assets WHERE id = ?', (asset_id,)).fetchone()

    conn.close()
    columns = get_columns()[1:]  # Exclude id for form fields
    display_columns = get_display_columns()[1:]
    return render_template('form.html', asset=asset, assets=assets, columns=columns,
                         display_columns=display_columns, current_id=asset_id)

@app.route('/notes')
def notes_view():
    conn = get_db()
    notes = conn.execute('SELECT * FROM notes ORDER BY date DESC').fetchall()
    conn.close()
    return render_template('notes.html', notes=notes)

@app.route('/api/asset/<int:asset_id>', methods=['PUT'])
def update_asset(asset_id):
    data = request.json
    conn = get_db()

    columns = get_columns()[1:]  # Exclude id
    set_clause = ', '.join([f'{col} = ?' for col in columns])
    values = [data.get(col, '') for col in columns]
    values.append(asset_id)

    conn.execute(f'UPDATE assets SET {set_clause} WHERE id = ?', values)
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/asset', methods=['POST'])
def create_asset():
    data = request.json
    conn = get_db()

    columns = get_columns()[1:]  # Exclude id
    placeholders = ', '.join(['?' for _ in columns])
    col_names = ', '.join(columns)
    values = [data.get(col, '') for col in columns]

    cursor = conn.execute(f'INSERT INTO assets ({col_names}) VALUES ({placeholders})', values)
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'id': new_id})

@app.route('/api/asset/<int:asset_id>', methods=['DELETE'])
def delete_asset(asset_id):
    conn = get_db()
    conn.execute('DELETE FROM assets WHERE id = ?', (asset_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/cell', methods=['POST'])
def update_cell():
    data = request.json
    asset_id = data['id']
    column = data['column']
    value = data['value']

    # Validate column name to prevent SQL injection
    valid_columns = get_columns()
    if column not in valid_columns:
        return jsonify({'success': False, 'error': 'Invalid column'}), 400

    conn = get_db()
    conn.execute(f'UPDATE assets SET {column} = ? WHERE id = ?', (value, asset_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/note', methods=['POST'])
def create_note():
    data = request.json
    conn = get_db()
    conn.execute('INSERT INTO notes (date, net_name, note) VALUES (?, ?, ?)',
                (data['date'], data.get('net_name', ''), data['note']))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/note/<int:note_id>', methods=['PUT'])
def update_note(note_id):
    data = request.json
    conn = get_db()
    conn.execute('UPDATE notes SET date = ?, net_name = ?, note = ? WHERE id = ?',
                (data['date'], data.get('net_name', ''), data['note'], note_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/note/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    conn = get_db()
    conn.execute('DELETE FROM notes WHERE id = ?', (note_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
