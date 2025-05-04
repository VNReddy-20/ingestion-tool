from flask import Flask, request, jsonify, render_template
import clickhouse_connect
import pandas as pd
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'Uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/connect', methods=['POST'])
def connect():
    try:
        source = request.form['source']
        if source == 'clickhouse':
            host = request.form['ch_host']
            port = request.form['ch_port']
            database = request.form['ch_database']
            user = request.form['ch_user']
            jwt_token = request.form['ch_jwt']
            client = clickhouse_connect.get_client(
                host=host, port=int(port), username=user, password=jwt_token, database=database, secure=(port in ['9440', '8443'])
            )
            tables = client.query('SHOW TABLES').result_rows
            return jsonify({'status': 'success', 'tables': [t[0] for t in tables]})
        elif source == 'flatfile':
            file = request.files['ff_file']
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            df = pd.read_csv(file_path)
            columns = df.columns.tolist()
            return jsonify({'status': 'success', 'tables': [filename], 'columns': columns})
        return jsonify({'status': 'error', 'message': 'Invalid source'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/columns', methods=['POST'])
def get_columns():
    try:
        source = request.form['source']
        table = request.form['table']
        if source == 'clickhouse':
            host = request.form['ch_host']
            port = request.form['ch_port']
            database = request.form['ch_database']
            user = request.form['ch_user']
            jwt_token = request.form['ch_jwt']
            client = clickhouse_connect.get_client(
                host=host, port=int(port), username=user, password=jwt_token, database=database, secure=(port in ['9440', '8443'])
            )
            columns = client.query(f'DESC {table}').result_rows
            return jsonify({'status': 'success', 'columns': [c[0] for c in columns]})
        elif source == 'flatfile':
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], table)
            df = pd.read_csv(file_path)
            return jsonify({'status': 'success', 'columns': df.columns.tolist()})
        return jsonify({'status': 'error', 'message': 'Invalid source'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/preview', methods=['POST'])
def preview():
    try:
        source = request.form['source']
        table = request.form['table']
        columns = request.form.getlist('columns')
        if not columns:
            return jsonify({'status': 'error', 'message': 'No columns selected'})
        if source == 'clickhouse':
            host = request.form['ch_host']
            port = request.form['ch_port']
            database = request.form['ch_database']
            user = request.form['ch_user']
            jwt_token = request.form['ch_jwt']
            client = clickhouse_connect.get_client(
                host=host, port=int(port), username=user, password=jwt_token, database=database, secure=(port in ['9440', '8443'])
            )
            query = f"SELECT {', '.join(columns)} FROM {table} LIMIT 100"
            result = client.query(query).result_rows
            return jsonify({'status': 'success', 'data': result, 'columns': columns})
        elif source == 'flatfile':
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], table)
            df = pd.read_csv(file_path, nrows=100)
            df = df[columns]
            return jsonify({'status': 'success', 'data': df.values.tolist(), 'columns': columns})
        return jsonify({'status': 'error', 'message': 'Invalid source'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/ingest', methods=['POST'])
def ingest():
    try:
        source = request.form['source']
        table = request.form['table']
        columns = request.form.getlist('columns')
        target = request.form['target']
        if not columns:
            return jsonify({'status': 'error', 'message': 'No columns selected'})
        
        if source == 'clickhouse':
            host = request.form['ch_host']
            port = request.form['ch_port']
            database = request.form['ch_database']
            user = request.form['ch_user']
            jwt_token = request.form['ch_jwt']
            client = clickhouse_connect.get_client(
                host=host, port=int(port), username=user, password=jwt_token, database=database, secure=(port in ['9440', '8443'])
            )
            query = f"SELECT {', '.join(columns)} FROM {table}"
            result = client.query(query)
            df = pd.DataFrame(result.result_rows, columns=columns)
            if target == 'flatfile':
                output_file = f"output_{table}.csv"
                df.to_csv(os.path.join(app.config['UPLOAD_FOLDER'], output_file), index=False)
                return jsonify({'status': 'success', 'record_count': len(df), 'message': f'Data saved to {output_file}'})
            return jsonify({'status': 'error', 'message': 'Invalid target'})
        
        elif source == 'flatfile':
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], table)
            df = pd.read_csv(file_path)
            df = df[columns]
            if target == 'clickhouse':
                host = request.form['ch_host']
                port = request.form['ch_port']
                database = request.form['ch_database']
                user = request.form['ch_user']
                jwt_token = request.form['ch_jwt']
                client = clickhouse_connect.get_client(
                    host=host, port=int(port), username=user, password=jwt_token, database=database, secure=(port in ['9440', '8443'])
                )
                table_name = table.split('.')[0]
                client.command(f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join([f'`{col}` String' for col in columns])}) ENGINE = MergeTree ORDER BY tuple()")
                client.insert_df(table_name, df)
                return jsonify({'status': 'success', 'record_count': len(df), 'message': f'Data inserted into {table_name}'})
            return jsonify({'status': 'error', 'message': 'Invalid target'})
        
        return jsonify({'status': 'error', 'message': 'Invalid source'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    app.run(debug=True)
    
