from flask import Flask, request, jsonify, render_template
import pandas as pd

app = Flask(__name__)

# Load data from CSV files
reviews_data = pd.read_csv('data/amazon-reviews.csv')
cities_data = pd.read_csv('data/us-cities.csv')

def firstQuery(city_name, limit):
    if city_name:
        reviews_in_city = reviews_data[reviews_data['city'] == city_name]
    else:
        reviews_in_city = reviews_data

    word_counts = reviews_in_city['review'].str.split(expand=True).stack().value_counts()

    popular_words = [{'term': word, 'popularity': count} for word, count in word_counts.head(limit).items()]

    return jsonify(popular_words)

def popQuery(city_name, limit):
    city_population_dict = cities_data.set_index('city')['population'].to_dict()
    if city_name:
        reviews_in_city = reviews_data[reviews_data['city'] == city_name]
    else:
        reviews_in_city = reviews_data

    word_counts = reviews_in_city['review'].str.split(expand=True).stack().value_counts()
    word_counts[:] = 0
    word_counts_dict = dict(word_counts)

    for i in word_counts_dict.keys():
        city_list = []
        for index, row in reviews_data.iterrows():
            if i in row['review'] and not row['city'] in city_list:
                city_list.append(row['city'])
                word_counts_dict[i] = word_counts_dict[i] + city_population_dict[row['city']]


    show_words = dict(sorted(word_counts_dict.items(), key=lambda item: item[1], reverse=True)[:limit])
    popular_words = []
    for i in show_words:
        popular_words.append({'term': i, 'popularity': str(show_words[i])})
    return jsonify(popular_words)


@app.route('/popular_words', methods=['GET'])
def get_popular_words():
    city_name = request.args.get('city')
    limit = int(request.args.get('limit'))
    isPop = request.args.get('pop')

    if isPop == 'population':
        print("population !!!!")
        return popQuery(city_name, limit)
    return firstQuery(city_name, limit)


@app.route('/substitute_words', methods=['POST'])
def substitute_words():
    print('substitute_words !!!!')
    data = request.get_json()
    word = data['word']
    substitute = data['substitute']
    print(type(word))
    affected_reviews = reviews_data['review'].str.contains(word).sum()
    # reviews_data['review'] = reviews_data['review'].str.replace(word, substitute)
    return jsonify({"affected_reviews": int(affected_reviews)})


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
