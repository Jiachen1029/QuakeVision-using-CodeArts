from flask import render_template, flash, redirect, url_for, request, jsonify, Response, abort
from app import app, db
from app.models import User, Earthquake, City, UploadLog
from flask_login import current_user, login_user, logout_user, login_required
from urllib.parse import urlparse
import urllib.request
import urllib.parse
from functools import wraps

from datetime import datetime
import io
import csv
import pandas as pd
import os
from werkzeug.utils import secure_filename
import json
from math import radians, cos, sin, asin, sqrt

# Global constants
CHINA_PROVINCES = ['北京', '天津', '河北', '山西', '内蒙古', '辽宁', '吉林', '黑龙江', '上海', '江苏', '浙江', '安徽', '福建', '江西', '山东', '河南', '湖北', '湖南', '广东', '广西', '海南', '重庆', '四川', '贵州', '云南', '西藏', '陕西', '甘肃', '青海', '宁夏', '新疆', '香港', '澳门', '台湾']
COMMON_COUNTRIES = ['日本', '印尼', '菲律宾', '美国', '智利', '俄罗斯', '巴布亚新几内亚', '斐济', '汤加', '新西兰', '墨西哥', '秘鲁', '阿富汗', '伊朗', '土耳其', '希腊', '意大利', '尼泊尔', '印度', '巴基斯坦', '缅甸', '瓦努阿图', '所罗门群岛']

def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles
    return c * r

def role_required(roles):
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if current_user.role not in roles:
                flash('您没有权限执行此操作')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def build_query():
    # Build query
    query = Earthquake.query

    # Date filter
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    if start_date:
        query = query.filter(Earthquake.time >= datetime.strptime(start_date, '%Y-%m-%d'))
    if end_date:
        # Add 23:59:59 to include the end date fully
        query = query.filter(Earthquake.time <= datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59))

    # Magnitude filter
    min_mag = request.args.get('min_mag', type=float)
    max_mag = request.args.get('max_mag', type=float)
    if min_mag is not None:
        query = query.filter(Earthquake.magnitude >= min_mag)
    if max_mag is not None:
        query = query.filter(Earthquake.magnitude <= max_mag)

    # Depth filter
    min_depth = request.args.get('min_depth', type=float)
    max_depth = request.args.get('max_depth', type=float)
    if min_depth is not None:
        query = query.filter(Earthquake.depth >= min_depth)
    if max_depth is not None:
        query = query.filter(Earthquake.depth <= max_depth)

    # Coordinates filter
    min_lon = request.args.get('min_lon', type=float)
    max_lon = request.args.get('max_lon', type=float)
    min_lat = request.args.get('min_lat', type=float)
    max_lat = request.args.get('max_lat', type=float)
    
    if min_lon is not None:
        query = query.filter(Earthquake.longitude >= min_lon)
    if max_lon is not None:
        query = query.filter(Earthquake.longitude <= max_lon)
    if min_lat is not None:
        query = query.filter(Earthquake.latitude >= min_lat)
    if max_lat is not None:
        query = query.filter(Earthquake.latitude <= max_lat)

    # Location scope
    location_scope = request.args.get('location_scope')
    if location_scope == 'china':
        # Filter by keywords for China
        from sqlalchemy import or_
        query = query.filter(or_(*[Earthquake.location.contains(k) for k in CHINA_PROVINCES]))
    elif location_scope == 'foreign':
        # Filter out records containing China keywords
        from sqlalchemy import and_
        query = query.filter(and_(*[~Earthquake.location.contains(k) for k in CHINA_PROVINCES]))

    # Keyword search
    keyword = request.args.get('keyword')
    if keyword:
        query = query.filter(Earthquake.location.contains(keyword))
        
    return query

@app.route('/')
@app.route('/index')
def index():
    # Get query parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    if per_page not in [20, 50, 100]:
        per_page = 20

    query = build_query()

    earthquakes = query.order_by(Earthquake.time.desc()).paginate(
        page=page, per_page=per_page, error_out=False)
    
    favorited_ids = set()
    if current_user.is_authenticated:
        favorited_ids = set(e.id for e in current_user.favorited_earthquakes)

    return render_template('index.html', title='主页', earthquakes=earthquakes.items, pagination=earthquakes, total=earthquakes.total, next_url=earthquakes.next_num, prev_url=earthquakes.prev_num, favorited_ids=favorited_ids)

@app.route('/export')
@login_required
def export_data():
    query = build_query()
    earthquakes = query.order_by(Earthquake.time.desc()).all()
    
    # Generate CSV
    output = io.StringIO()
    # Add BOM for Excel compatibility
    output.write('\ufeff')
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['ID', '发震时间', '经度', '纬度', '深度(km)', '震级(M)', '位置', '类型'])
    
    # Write data
    for eq in earthquakes:
        writer.writerow([
            eq.id,
            eq.time.strftime('%Y-%m-%d %H:%M:%S'),
            eq.longitude,
            eq.latitude,
            eq.depth,
            eq.magnitude,
            eq.location,
            eq.event_type
        ])
        
    output.seek(0)
    
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=earthquakes_export.csv"}
    )

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user is None or not user.check_password(password):
            flash('用户名或密码错误')
            return redirect(url_for('login'))
        login_user(user)
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='登录')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('两次输入的密码不一致')
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=username).first():
            flash('用户名已存在')
            return redirect(url_for('register'))
        
        user = User(username=username, role='ROLE_USER')
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('注册成功，请登录')
        return redirect(url_for('login'))
    return render_template('register.html', title='注册')

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        old_password = request.form['old_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if not current_user.check_password(old_password):
            flash('原密码错误')
            return redirect(url_for('profile'))
        
        if new_password != confirm_password:
            flash('两次输入的新密码不一致')
            return redirect(url_for('profile'))
        
        current_user.set_password(new_password)
        db.session.commit()
        flash('密码修改成功')
        return redirect(url_for('profile'))
    return render_template('profile.html', title='个人中心')

@app.route('/admin')
@role_required(['ROLE_ADMIN'])
def admin_dashboard():
    users = User.query.all()
    return render_template('admin.html', title='管理员面板', users=users)

@app.route('/admin/add_user', methods=['POST'])
@role_required(['ROLE_ADMIN'])
def admin_add_user():
    username = request.form['username']
    password = request.form['password']
    role = request.form['role']

    if User.query.filter_by(username=username).first():
        flash('用户名已存在')
        return redirect(url_for('admin_dashboard'))
    
    user = User(username=username, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    flash(f'用户 {username} 添加成功')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_user/<int:id>', methods=['POST'])
@role_required(['ROLE_ADMIN'])
def admin_delete_user(id):
    user = User.query.get_or_404(id)
    if user.id == current_user.id:
        flash('不能删除自己')
        return redirect(url_for('admin_dashboard'))
    
    db.session.delete(user)
    db.session.commit()
    flash(f'用户 {user.username} 已删除')
    return redirect(url_for('admin_dashboard'))

@app.route('/upload', methods=['GET', 'POST'])
@role_required(['ROLE_STAFF', 'ROLE_ADMIN'])
def upload_data():
    # 重定向到新的统一页面
    return redirect(url_for('upload_manage'))

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@role_required(['ROLE_STAFF', 'ROLE_ADMIN'])
def edit_data(id):
    earthquake = Earthquake.query.get_or_404(id)
    if request.method == 'POST':
        try:
            earthquake.time = datetime.strptime(request.form['time'], '%Y-%m-%d %H:%M:%S')
        except ValueError:
            # Try parsing without seconds if user removed them or datepicker format varies
            try:
                earthquake.time = datetime.strptime(request.form['time'], '%Y-%m-%d')
            except:
                flash('日期格式错误，应为 YYYY-MM-DD HH:MM:SS')
                return render_template('edit.html', title='编辑数据', earthquake=earthquake)
                
        earthquake.magnitude = float(request.form['magnitude'])
        earthquake.latitude = float(request.form['latitude'])
        earthquake.longitude = float(request.form['longitude'])
        earthquake.depth = float(request.form['depth'])
        earthquake.location = request.form['location']
        earthquake.event_type = request.form['event_type']
        
        db.session.commit()
        flash('数据已更新')
        return redirect(url_for('index'))
    return render_template('edit.html', title='编辑数据', earthquake=earthquake)

@app.route('/delete/<int:id>', methods=['POST'])
@role_required(['ROLE_STAFF', 'ROLE_ADMIN'])
def delete_data(id):
    earthquake = Earthquake.query.get_or_404(id)
    db.session.delete(earthquake)
    db.session.commit()
    flash('数据已删除')
    return redirect(url_for('index'))



@app.route('/api/data')
@login_required
def get_data():
    # API for map visualization (return filtered data)
    query = build_query()
    earthquakes = query.all()
    return jsonify([eq.to_dict() for eq in earthquakes])

@app.route('/map')
@login_required
def map_view():
    # Pass query parameters to the template so JS can fetch filtered data
    return render_template('map.html', title='地震地图可视化')

@app.route('/city_risk')
@login_required
def city_risk():
    return render_template('city_risk.html', title='城市地震风险评估')

@app.route('/api/nearby_earthquakes')
@login_required
def nearby_earthquakes():
    try:
        lat = float(request.args.get('lat'))
        lon = float(request.args.get('lon'))
        max_radius = 150  # 最大搜索半径150km
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid parameters'}), 400

    # 1. Rough bounding box filter (1 degree lat ~= 111km)
    lat_delta = max_radius / 111.0 * 1.2 
    lon_delta = max_radius / (111.0 * cos(radians(lat))) * 1.2 if abs(lat) < 90 else 180

    query = Earthquake.query.filter(
        Earthquake.latitude.between(lat - lat_delta, lat + lat_delta),
        Earthquake.longitude.between(lon - lon_delta, lon + lon_delta)
    )
    
    candidates = query.all()
    
    # 分层统计（包含震级加权）
    results_50 = []   # 0-50km
    results_100 = []  # 50-100km
    results_150 = []  # 100-150km
    
    max_mag_50 = 0
    max_mag_100 = 0
    max_mag_150 = 0
    max_mag_total = 0
    
    # 震级加权求和（用于综合评估震级影响）
    mag_weight_50 = 0
    mag_weight_100 = 0
    mag_weight_150 = 0
    
    for eq in candidates:
        dist = haversine(lon, lat, eq.longitude, eq.latitude)
        eq_dict = eq.to_dict()
        eq_dict['distance'] = round(dist, 2)
        
        if dist <= 50:
            results_50.append(eq_dict)
            if eq.magnitude > max_mag_50:
                max_mag_50 = eq.magnitude
            # 震级越大，权重指数增长（使用平方）
            if eq.magnitude >= 3.0:
                mag_weight_50 += (eq.magnitude - 2) ** 2
        elif dist <= 100:
            results_100.append(eq_dict)
            if eq.magnitude > max_mag_100:
                max_mag_100 = eq.magnitude
            if eq.magnitude >= 3.0:
                mag_weight_100 += (eq.magnitude - 2) ** 2
        elif dist <= 150:
            results_150.append(eq_dict)
            if eq.magnitude > max_mag_150:
                max_mag_150 = eq.magnitude
            if eq.magnitude >= 3.0:
                mag_weight_150 += (eq.magnitude - 2) ** 2
        
        if dist <= 150 and eq.magnitude > max_mag_total:
            max_mag_total = eq.magnitude
    
    # 加权风险评分计算（震级敏感版本）
    # 基础分: 10分
    # 综合考虑：地震次数（对数）+ 震级权重（平方）+ 最大震级
    
    import math
    score = 10.0
    
    # 1. 50km内地震影响 (权重最高)
    count_50 = len(results_50)
    if count_50 > 0:
        # 频率惩罚：对数避免暴跌
        score -= math.log10(count_50 + 1) * 0.8
        # 震级累积惩罚：所有地震的震级平方和
        score -= math.log10(mag_weight_50 + 1) * 0.6
        # 最大震级惩罚：指数增长
        if max_mag_50 >= 4.0:
            score -= (max_mag_50 - 3) ** 1.5 * 0.5
    
    # 2. 100km内地震影响 (中等权重)
    count_100 = len(results_100)
    if count_100 > 0:
        score -= math.log10(count_100 + 1) * 0.5
        score -= math.log10(mag_weight_100 + 1) * 0.4
        if max_mag_100 >= 4.0:
            score -= (max_mag_100 - 3) ** 1.35 * 0.3
    
    # 3. 150km内地震影响 (较低权重)
    count_150 = len(results_150)
    if count_150 > 0:
        score -= math.log10(count_150 + 1) * 0.3
        score -= math.log10(mag_weight_150 + 1) * 0.2
        if max_mag_150 >= 4.0:
            score -= (max_mag_150 - 3) ** 1.2 * 0.15
    
    # 限制分数范围（保证最低1.0分）
    if score < 1.0: score = 1.0
    if score > 10: score = 10
    
    # 合并所有地震数据
    all_earthquakes = results_50 + results_100 + results_150
    
    return jsonify({
        'earthquakes': all_earthquakes,
        'stats': {
            'count_50': count_50,
            'count_100': count_100,
            'count_150': count_150,
            'count_total': len(all_earthquakes),
            'max_mag_50': max_mag_50,
            'max_mag_100': max_mag_100,
            'max_mag_150': max_mag_150,
            'max_mag_total': max_mag_total,
            'score': round(score, 1)
        }
    })

@app.route('/api/search_city')
@login_required
def search_city():
    city_name = request.args.get('q')
    if not city_name:
        return jsonify({'error': 'Missing city name'}), 400
    
    # 1. Check database
    city = City.query.filter_by(name=city_name).first()
    if city:
        return jsonify(city.to_dict())
    
    # 2. Fetch from Nominatim
    try:
        url = f"https://nominatim.openstreetmap.org/search?format=json&q={urllib.parse.quote(city_name)}"
        # Add User-Agent to comply with Nominatim usage policy
        req = urllib.request.Request(url, headers={'User-Agent': 'EarthquakeDB/1.0'})
        
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            
            if not data:
                return jsonify({'error': 'City not found'}), 404
            
            result = data[0]
            lat = float(result['lat'])
            lon = float(result['lon'])
            display_name = result['display_name'].split(',')[0]
            
            # 3. Save to database
            new_city = City(name=city_name, display_name=display_name, latitude=lat, longitude=lon)
            db.session.add(new_city)
            db.session.commit()
            
            return jsonify(new_city.to_dict())
            
    except Exception as e:
        print(f"Geocoding error: {e}")
        return jsonify({'error': 'Geocoding service unavailable'}), 503

@app.route('/statistics')
@login_required
def statistics():
    query = build_query()
    # Fetch data for statistics (limit to avoid memory issues if too large, but for stats we usually need all)
    # Using pandas to process
    earthquakes = query.all()
    
    if not earthquakes:
        flash('当前筛选条件下没有数据，无法生成统计图表')
        return redirect(url_for('index', **request.args))

    data = [eq.to_dict() for eq in earthquakes]
    df = pd.DataFrame(data)
    
    # 1. Magnitude Distribution
    # Bins: 3-4, 4-5, 5-6, 6-7, >=7
    bins = [3, 4, 5, 6, 7, 10]
    labels = ['3-4', '4-5', '5-6', '6-7', '≥7']
    df['mag_cat'] = pd.cut(df['magnitude'], bins=bins, labels=labels, right=False)
    mag_counts = df['mag_cat'].value_counts().sort_index()
    
    # 2. Depth Distribution
    # Bins: 0-10, 10-30, 30-70, 70-300, >300
    depth_bins = [0, 10, 30, 70, 300, 1000]
    depth_labels = ['0-10km', '10-30km', '30-70km', '70-300km', '>300km']
    df['depth_cat'] = pd.cut(df['depth'], bins=depth_bins, labels=depth_labels, right=False)
    depth_counts = df['depth_cat'].value_counts().sort_index()

    # 3. Time Trend (Daily/Monthly/Yearly)
    # We'll do Monthly trend for better visibility usually, or Yearly if span is large
    df['time'] = pd.to_datetime(df['time'])
    # Determine frequency based on time span
    time_span = df['time'].max() - df['time'].min()
    if time_span.days > 365 * 5:
        freq = 'Y' # Yearly
        time_format = '%Y'
    elif time_span.days > 30:
        freq = 'M' # Monthly
        time_format = '%Y-%m'
    else:
        freq = 'D' # Daily
        time_format = '%Y-%m-%d'
        
    time_counts = df.set_index('time').resample(freq).size()
    time_labels = time_counts.index.strftime(time_format).tolist()
    
    # 4. Location Summary (Top Provinces/Areas)
    
    def extract_province(loc):
        for p in CHINA_PROVINCES:
            if p in loc:
                return p
        for c in COMMON_COUNTRIES:
            if c in loc:
                return c
        return '国外其他'

    df['province'] = df['location'].apply(extract_province)
    
    # Helper to check if location is China
    def is_china(loc):
        for p in CHINA_PROVINCES:
            if p in loc:
                return True
        return False

    df['is_china'] = df['location'].apply(is_china)

    # Calculate 3 sets of stats
    # 1. All
    loc_counts_all = df['province'].value_counts().head(10)
    
    # 2. China Only
    loc_counts_china = df[df['is_china'] == True]['province'].value_counts().head(10)
    
    # 3. Foreign Only
    loc_counts_foreign = df[df['is_china'] == False]['province'].value_counts().head(10)

    stats_data = {
        'mag_labels': mag_counts.index.tolist(),
        'mag_values': mag_counts.values.tolist(),
        'depth_labels': depth_counts.index.tolist(),
        'depth_values': depth_counts.values.tolist(),
        'time_labels': time_labels,
        'time_values': time_counts.values.tolist(),
        'loc_labels': loc_counts_all.index.tolist(),
        'loc_values': loc_counts_all.values.tolist(),
        'loc_labels_china': loc_counts_china.index.tolist(),
        'loc_values_china': loc_counts_china.values.tolist(),
        'loc_labels_foreign': loc_counts_foreign.index.tolist(),
        'loc_values_foreign': loc_counts_foreign.values.tolist(),
        'total_count': len(df)
    }

    return render_template('statistics.html', title='统计分析', stats=stats_data)

@app.route('/favorite/<int:id>', methods=['POST'])
@login_required
def favorite_earthquake(id):
    earthquake = Earthquake.query.get_or_404(id)
    current_user.favorite(earthquake)
    db.session.commit()
    return jsonify({'status': 'success', 'action': 'favorited'})

@app.route('/unfavorite/<int:id>', methods=['POST'])
@login_required
def unfavorite_earthquake(id):
    earthquake = Earthquake.query.get_or_404(id)
    current_user.unfavorite(earthquake)
    db.session.commit()
    return jsonify({'status': 'success', 'action': 'unfavorited'})

@app.route('/my_favorites')
@login_required
def my_favorites():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    if per_page not in [20, 50, 100]:
        per_page = 20
    
    query = current_user.favorited_earthquakes.order_by(Earthquake.time.desc())
    
    earthquakes = query.paginate(page=page, per_page=per_page, error_out=False)
    
    favorited_ids = set(e.id for e in earthquakes.items)
    
    return render_template('my_favorites.html', title='我的收藏', 
                           earthquakes=earthquakes.items, 
                           pagination=earthquakes, 
                           total=earthquakes.total, 
                           next_url=earthquakes.next_num, 
                           prev_url=earthquakes.prev_num,
                           favorited_ids=favorited_ids)

@app.route('/upload_manage', methods=['GET', 'POST'])
@role_required(['ROLE_STAFF', 'ROLE_ADMIN'])
def upload_manage():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('没有文件部分')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('没有选择文件')
            return redirect(request.url)
        if file and (file.filename.endswith('.xlsx') or file.filename.endswith('.xls')):
            try:
                df = pd.read_excel(file)
                # Drop duplicates in the uploaded file
                df.drop_duplicates(inplace=True)
                
                count = 0
                for index, row in df.iterrows():
                    # Map columns - adjust these names based on your actual Excel file
                    try:
                        # Flexible column name matching
                        time_col = next((c for c in df.columns if '时间' in c or '时刻' in c), None)
                        lon_col = next((c for c in df.columns if '经度' in c), None)
                        lat_col = next((c for c in df.columns if '纬度' in c), None)
                        depth_col = next((c for c in df.columns if '深度' in c), None)
                        mag_col = next((c for c in df.columns if '震级' in c), None)
                        loc_col = next((c for c in df.columns if '位置' in c or '地点' in c), None)
                        type_col = next((c for c in df.columns if '类型' in c), None)

                        if not (time_col and lon_col and lat_col and depth_col and mag_col and loc_col):
                            continue

                        time_val = pd.to_datetime(row[time_col])
                        # Check for duplicates in DB
                        exists = Earthquake.query.filter_by(
                            time=time_val,
                            longitude=float(row[lon_col]),
                            latitude=float(row[lat_col]),
                            magnitude=float(row[mag_col])
                        ).first()
                        
                        if not exists:
                            eq = Earthquake(
                                time=time_val,
                                longitude=float(row[lon_col]),
                                latitude=float(row[lat_col]),
                                depth=float(row[depth_col]),
                                magnitude=float(row[mag_col]),
                                location=str(row[loc_col]),
                                event_type=str(row[type_col]) if type_col else '天然地震'
                            )
                            db.session.add(eq)
                            count += 1
                    except Exception as e:
                        print(f"Error parsing row {index}: {e}")
                        continue
                
                db.session.commit()
                
                # 记录上传日志
                upload_log = UploadLog(
                    user_id=current_user.id,
                    filename=file.filename,
                    records_count=count,
                    status='success'
                )
                db.session.add(upload_log)
                db.session.commit()
                
                flash(f'成功导入 {count} 条新数据')
            except Exception as e:
                # 记录失败日志
                upload_log = UploadLog(
                    user_id=current_user.id,
                    filename=file.filename if file else 'unknown',
                    records_count=0,
                    status='failed'
                )
                db.session.add(upload_log)
                db.session.commit()
                
                flash(f'导入失败: {str(e)}')
        else:
            flash('只支持 Excel 文件 (.xlsx, .xls)')
            
        return redirect(url_for('upload_manage'))
    
    # 处理日志查看
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    if per_page not in [20, 50, 100]:
        per_page = 20
    
    # 所有职员和管理员都可以看所有日志
    query = UploadLog.query.order_by(UploadLog.created_at.desc())
    
    logs = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('upload_manage.html', title='上传数据与日志',
                           logs=logs.items,
                           pagination=logs,
                           total=logs.total,
                           next_url=logs.next_num,
                           prev_url=logs.prev_num)

@app.route('/upload_logs')
@role_required(['ROLE_STAFF', 'ROLE_ADMIN'])
def upload_logs():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    if per_page not in [20, 50, 100]:
        per_page = 20
    
    # 所有职员和管理员都可以看所有日志
    query = UploadLog.query.order_by(UploadLog.created_at.desc())
    
    logs = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('upload_logs.html', title='上传日志',
                           logs=logs.items,
                           pagination=logs,
                           total=logs.total,
                           next_url=logs.next_num,
                           prev_url=logs.prev_num)
