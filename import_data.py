import pandas as pd
from app import app, db
from app.models import Earthquake
from datetime import datetime

def import_excel(file_path):
    print(f"Reading file: {file_path}...")
    try:
        df = pd.read_excel(file_path)
        # Columns: ['序号', '发震日期（北京时间）', '经度(°)', '纬度(°)', '震源深度(Km)', '震级(M)', '震中位置', '事件类型']
        
        with app.app_context():
            # Clear existing data to avoid duplicates during development
            # db.session.query(Earthquake).delete()
            
            count = 0
            for index, row in df.iterrows():
                # Check if record with same original_id exists
                existing = Earthquake.query.filter_by(original_id=row['序号']).first()
                if existing:
                    continue

                time_val = row['发震日期（北京时间）']
                # Ensure time_val is a datetime object
                if isinstance(time_val, str):
                    try:
                        time_val = datetime.strptime(time_val, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        try:
                             time_val = datetime.strptime(time_val, '%Y-%m-%d %H:%M')
                        except:
                            print(f"Skipping row {index}: Invalid date format {time_val}")
                            continue
                
                eq = Earthquake(
                    original_id=row['序号'],
                    time=time_val,
                    longitude=row['经度(°)'],
                    latitude=row['纬度(°)'],
                    depth=row['震源深度(Km)'],
                    magnitude=row['震级(M)'],
                    location=row['震中位置'],
                    event_type=row['事件类型']
                )
                db.session.add(eq)
                count += 1
            
            db.session.commit()
            print(f"Successfully imported {count} new records.")
            
    except Exception as e:
        print(f"Error importing data: {e}")

if __name__ == '__main__':
    import_excel('速报目录.xls')
