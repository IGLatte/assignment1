import re
import math, time
import numpy as np
import redis
import json
from flask import Flask, request, jsonify, render_template
from azure.cosmos import CosmosClient
from sklearn.neighbors import NearestNeighbors
from collections import Counter

redis_passwd = "tuk2O44M3LfJIwJLYfI6td5qbbnCEdxHBAzCaMTiS5s="
# "Host name" in properties
redis_host = "yhyredis.redis.cache.windows.net"
# SSL Port
redis_port = 6380

cache = redis.StrictRedis(
    host=redis_host, port=redis_port,
    db=0, password=redis_passwd,
    ssl=True,
)

app = Flask(__name__)

# Azure Cosmos DB 配置
url = "https://tutorial-uta-cse6332.documents.azure.com:443/"
key = "fSDt8pk5P1EH0NlvfiolgZF332ILOkKhMdLY6iMS2yjVqdpWx4XtnVgBoJBCBaHA8PIHnAbFY4N9ACDbMdwaEw=="
client = CosmosClient(url, credential=key)
database = client.get_database_client('tutorial')
cities = database.get_container_client('us_cities')
reviews = database.get_container_client('reviews')

# 加载停用词
with open("data/stopwords.txt", "r", encoding="utf-8") as file:
    stopwords = set(file.read().splitlines())


# 根据城市的名字，得到reviews中的单词列表
def get_most_words(city_list, n):
    counts = Counter()
    pattern = r'\b[a-zA-Z]+\b'  # 匹配仅包含字母的单词的正则表达式
    # 将符合条件的所有review整理成列表
    review_query = f"SELECT reviews.review FROM reviews WHERE reviews.city = '{city_list[0]['city']}'"
    for i in range(len(city_list)):
        if i == 0:
            continue
        cityname = city_list[i]['city']
        conditions = f" OR reviews.city = '{cityname}'"
        review_query += conditions
    review_items = list(reviews.query_items(review_query, enable_cross_partition_query=True))
    # 统计列表中的所有word词频，过滤停用词
    for review_item in review_items:
        words = re.findall(pattern, review_item['review'].lower())
        for word in words:
            if word not in stopwords:
                counts[word] += 1
    most_words = counts.most_common(n)

    return most_words


# 需求11
@app.route('/radar_reviews', methods=['GET'])
def radar_reviews():
    try:
        start_time = time.time()

        # 获取请求参数
        classes = int(request.args.get('classes'))
        k = int(request.args.get('k'))

        cache_key = f"radar_reviews:{classes}:{k}"
        cached_data = cache.get(cache_key)

        if cached_data:
            # Data is in cache
            cache_result = json.loads(cached_data)
            # 计算响应时间
            response_time = int((time.time() - start_time) * 1000)
            response = {
                'result': cache_result[1],
                'labels': cache_result[0],
                'response_time': response_time,
            }
        else:
            # 计算欧氏距离矩阵,使用kNN算法进行聚类
            city_items, city_coordinates = redis_knn()
            distances = np.linalg.norm(np.array(city_coordinates) - np.array(city_coordinates)[:, None], axis=-1)
            knn = NearestNeighbors(n_neighbors=k)
            knn.fit(distances)
            _, indices = knn.kneighbors()

            cache_result = []
            result = []
            labels = []

            class_word_data = []
            # 遍历每个类别
            for i in range(classes):
                # 这个类别中的城市列表
                class_cities = [city_items[j] for j in indices[i]]
                word_list = get_most_words(class_cities, 10)
                class_word_data.append(word_list)
                if i == 0 :
                    labels = [item[0] for item in word_list]
                else:
                    for item in word_list:
                        if item[0] not in labels:
                            labels.append(item[0])

            for i in range(len(class_word_data)):
                word_result = [0] * len(labels)
                for word_data in class_word_data[i]:
                    word_result[labels.index(word_data[0])] = word_data[1]
                result.append({
                    'label': 'class_' + str(i + 1),
                    'word_data': word_result
                })
            cache_result.append(labels)
            cache_result.append(result)
            cache.setex(cache_key, 3600, json.dumps(cache_result))

            # 计算响应时间
            response_time = int((time.time() - start_time) * 1000)

            response = {
                'result': result,
                'labels': labels,
                'response_time': response_time
            }

        return jsonify(response)
    except Exception as e:
        return jsonify({'error': str(e)})


# cache pre_distances
def redis_knn():
    cache_key = "redis_distance"
    cached_data = cache.get(cache_key)
    if cached_data:
        result = json.loads(cached_data)
        return result[0]['city'], result[1]['coords']
    else:
        # 提取经纬度
        city_query = 'SELECT c.city, c.lat, c.lng, c.state, c.population FROM c'
        city_items = list(cities.query_items(city_query, enable_cross_partition_query=True))
        city_coordinates = [(float(item['lat']), float(item['lng'])) for item in city_items]
        result = [{'city': city_items}, {'coords': city_coordinates}]
        cache.setex(cache_key, 3600, json.dumps(result))
        print('city_items and city_coordinates cached successfully!')
        return city_items, city_coordinates

# 需求11
def get_average_score(city_list):
    weight = 0
    population = 0
    for i in range(len(city_list)):
        cityname = city_list[i]['city']
        weight_query = f"SELECT c.population FROM c WHERE c.city = '{cityname}'"
        weight_items = list(cities.query_items(weight_query, enable_cross_partition_query=True))
        score = 0
        score_query = f"SELECT c.score FROM c WHERE c.city = '{cityname}'"
        score_items = list(reviews.query_items(score_query, enable_cross_partition_query=True))
        for score_item in score_items:
            score += float(score_item['score'])
        score /= len(score_items)
        weight += score * float(weight_items[0]['population'])
        population += float(weight_items[0]['population'])

    return weight / population

# 需求11,饼状图
@app.route('/data/knn_reviews', methods=['GET'])
def get_knn_reviews():
    try:
        start_time = time.time()
        # 获取请求参数
        classes = int(request.args.get('classes'))
        k = int(request.args.get('k'))

        cache_key = f"reviews:{classes}:{k}"
        cached_data = cache.get(cache_key)
        if cached_data:
            # Data is in cache
            result = json.loads(cached_data)
            # 计算响应时间
            response_time = int((time.time() - start_time) * 1000)
            response = {
                'result': result,
                'response_time': response_time,

            }
        else:
            # 计算欧氏距离矩阵,使用kNN算法进行聚类
            city_items, city_coordinates = redis_knn()
            distances = np.linalg.norm(np.array(city_coordinates) - np.array(city_coordinates)[:, None], axis=-1)
            knn = NearestNeighbors(n_neighbors=k)
            knn.fit(distances)
            _, indices = knn.kneighbors()
            result = []
            # 遍历每个类别
            for i in range(classes):
                class_cities = [city_items[j] for j in indices[i]]
                total_pop = 0
                # 为每个类计算总人口
                for j in indices[i]:
                    total_pop = int(city_items[j]['population'])
                result.append({'label': 'class_' + str(i + 1), 'population': total_pop, 'num': len(class_cities), 'name': class_cities[0]['city'], 'state': class_cities[0]['state'], 'score': get_average_score(class_cities)})
            cache.setex(cache_key, 3600, json.dumps(result))
            # 计算响应时间
            response_time = int((time.time() - start_time) * 1000)

            response = {
                'result': result,
                'response_time': response_time,
            }
        return jsonify(response)
    except Exception as e:
        return jsonify({'error': str(e)})


# 查询平均分
@app.route('/aver_score', methods=['GET'])
def average_score():
    # 计算响应时间
    start_time = time.time()
    city_name = request.args.get('city')
    state_name = request.args.get('state')
    page = int(request.args.get('page'))

    # 分页
    page_size = 10
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size

    cache_key = f"average_score:{city_name}:{state_name}:{page}"
    cached_data = cache.get(cache_key)

    if cached_data:
        # Data is in cache
        cities_distance = json.loads(cached_data)
        from_cache = True
        response = {
            "closest_cities": cities_distance,
            "response_time_ms": int((time.time() - start_time) * 1000),
            "cached": from_cache
        }
    else:
        # 查询给定城市的经纬度信息
        query = f"SELECT c.lat, c.lng FROM c WHERE c.city = '{str(city_name)}' AND c.state = '{str(state_name)}'"
        target_city = list(cities.query_items(query, enable_cross_partition_query=True))

        if not target_city:
            return jsonify({"error": "City not found"}), 404

        city_lat, city_lng = float(target_city[0]['lat']), float(target_city[0]['lng'])

        # 计算与其他城市的欧拉距离保存并排序
        query = f"SELECT c.city, c.lat, c.lng FROM c WHERE c.city != '{str(city_name)}' and c.state != '{str(state_name)}'"
        result = list(cities.query_items(query, enable_cross_partition_query=True))
        closest_cities = sorted(result, key=lambda c: math.sqrt(
            (float(c['lat']) - city_lat) ** 2 + (float(c['lng']) - city_lng) ** 2))

        # 当前页需要的十条数据
        cities_distance = closest_cities[start_idx:end_idx]
        for city in cities_distance:
            city['score'] = get_score(city['city'])

        cache.setex(cache_key, 3600, json.dumps(cities_distance))
        response = {
            "closest_cities": cities_distance,
            "response_time_ms": int((time.time() - start_time) * 1000),
            "cached": False
        }
    return jsonify(response), 200


# 查询距离
@app.route('/distance', methods=['GET'])
def distance():
    # 计算响应时间
    start_time = time.time()
    city_name = request.args.get('city')
    state_name = request.args.get('state')
    page = int(request.args.get('page'))

    # 分页
    page_size = 50
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size

    cache_key = f"city_distance:{city_name}:{state_name}"
    cached_data = cache.get(cache_key)

    if cached_data:
        # Data is in cache
        cities_distance = json.loads(cached_data)[start_idx:end_idx]
        from_cache = True
        response = {
            "closest_cities": cities_distance,
            "response_time_ms": int((time.time() - start_time) * 1000),
            "cached": from_cache
        }

    else:
        # 查询给定城市的经纬度信息
        query = f"SELECT c.lat, c.lng FROM c WHERE c.city = '{str(city_name)}' AND c.state = '{str(state_name)}'"
        target_city = list(cities.query_items(query, enable_cross_partition_query=True))

        if not target_city:
            return jsonify({"error": "City not found"}), 404

        city_lat, city_lng = float(target_city[0]['lat']), float(target_city[0]['lng'])

        # 计算与其他城市的欧拉距离保存并排序
        query = f"SELECT c.city, c.lat, c.lng FROM c WHERE c.city != '{str(city_name)}' and c.state != '{str(state_name)}'"
        result = list(cities.query_items(query, enable_cross_partition_query=True))

        closest_cities = sorted(result, key=lambda c: math.sqrt(
            (float(c['lat']) - city_lat) ** 2 + (float(c['lng']) - city_lng) ** 2))
        for city in closest_cities:
            city['distance'] = math.sqrt((float(city['lat']) - city_lat) ** 2 + (float(city['lng']) - city_lng) ** 2)

        cache.setex(cache_key, 3600, json.dumps(closest_cities))

        cities_distance = closest_cities[start_idx:end_idx]

        response = {
            "closest_cities": cities_distance,
            "response_time_ms": int((time.time() - start_time) * 1000),
            "cached": False
        }

    return jsonify(response), 200


# 获得平均分
def get_score(city_name):
    review_query = f"SELECT reviews.score FROM reviews WHERE reviews.city = '{city_name}'"
    score_items = list(reviews.query_items(review_query, enable_cross_partition_query=True))
    if not score_items:
        return 0
    total_score = 0
    length = 0
    for score in score_items:
        total_score += int(score['score'])
        length += 1

    return total_score / length


@app.route('/clear_cache', methods=['GET'])
def clear_cache():
    cache.flushall()
    return jsonify({'message': 'Cache cleared successfully'}), 200


@app.route('/')
def welcome_page():
    return render_template('welcome.html')


@app.route('/city')
def city():
    return render_template('city.html')


@app.route('/score')
def score():
    return render_template('score.html')


@app.route('/review')
def review():
    return render_template('review.html')


@app.route('/radar')
def radar():
    return render_template('radar.html')


if __name__ == '__main__':
    app.run(debug=True)
