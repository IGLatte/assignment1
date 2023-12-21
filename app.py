import re
import math, time
import numpy as np
from flask import Flask, request, jsonify, render_template
from azure.cosmos import CosmosClient
from collections import Counter
from sklearn.neighbors import NearestNeighbors

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
def get_words_list(city_list, n):
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
    sorted_counts = counts.most_common(n)

    return sorted_counts


# 需求12
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


# 需求11
@app.route('/data/knn_reviews', methods=['GET'])
def get_knn_reviews():
    try:
        start_time = time.time()

        # 获取请求参数
        classes = int(request.args.get('classes'))
        k = int(request.args.get('k'))
        words = int(request.args.get('words'))

        # 提取经纬度
        city_query = 'SELECT c.city, c.lat, c.lng FROM c'
        city_items = list(cities.query_items(city_query, enable_cross_partition_query=True))
        city_coordinates = [(float(item['lat']), float(item['lng'])) for item in city_items]

        # 计算欧氏距离矩阵
        distances = np.linalg.norm(np.array(city_coordinates) - np.array(city_coordinates)[:, None], axis=-1)

        # 使用kNN算法进行聚类
        knn = NearestNeighbors(n_neighbors=k)
        knn.fit(distances)
        _, indices = knn.kneighbors()

        result = {}
        # 遍历每个类别
        for i in range(classes):
            # 这个类别中的城市列表
            class_cities = [city_items[j] for j in indices[i]]

            result['class_' + str(i + 1)] = {
                'center_city': class_cities[0],
                'cities': class_cities,
                'most_popular_words': get_words_list(class_cities, words),
                'weighted_average_score': get_average_score(class_cities)
            }

        # 计算响应时间
        response_time = int((time.time() - start_time) * 1000)

        return jsonify({
            'result': result,
            'response_time': response_time
        })
    except Exception as e:
        return jsonify({'error': str(e)})


# 需求10
@app.route('/stat/closest_cities', methods=['GET'])
def closest_cities():
    try:
        city_name = request.args.get('city')
        page_size = int(request.args.get('page_size', 50))
        page = int(request.args.get('page', 0))

        # 查询给定城市的经纬度信息
        query = f"SELECT c.lat, c.lng FROM c WHERE c.city = '{str(city_name)}'"
        result = list(cities.query_items(query, enable_cross_partition_query=True))

        if not result:
            return jsonify({"error": "City not found"}), 404

        city_lat, city_lng = float(result[0]['lat']), float(result[0]['lng'])

        # 计算与其他城市的欧拉距离保存并排序
        query = f"SELECT c.city, c.lat, c.lng FROM c WHERE c.city != '{str(city_name)}'"
        result = list(cities.query_items(query, enable_cross_partition_query=True))
        closest_cities = sorted(result, key=lambda c: math.sqrt(
            (float(c['lat']) - city_lat) ** 2 + (float(c['lng']) - city_lng) ** 2))
        for city in closest_cities:
            city['distance'] = math.sqrt((float(city['lat']) - city_lat) ** 2 + (float(city['lng']) - city_lng) ** 2)

        # 分页
        start_idx = page * page_size
        end_idx = start_idx + page_size
        paginated_cities = closest_cities[start_idx:end_idx]

        # 计算响应时间
        start_time = time.time()
        response = {
            "closest_cities": paginated_cities,
            "response_time_ms": int((time.time() - start_time) * 1000)
        }

        return jsonify(response), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/')
def welcome():
    return render_template('welcome.html')


@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/review')
def review():
    return render_template('review.html')


if __name__ == '__main__':
    app.run(debug=True)
