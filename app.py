import csv
from flask import Flask, render_template, url_for, request, jsonify
app = Flask(__name__)

PAGE_SIZE = 6

@app.route('/')
def index():
    student_name = "Yang Heyu"  # 替换为学生的姓名
    student_id = "75979"  # 替换为学生的学号
    photo_url = url_for('static', filename='yhy.jpeg')  # 替换为学生的照片 URL

    return render_template('index.html', name=student_name, id=student_id, photo_url=photo_url)
@app.route('/reviews')
def reviews():
    page = int(request.args.get('page', 1))  # 获取当前页数，默认为第一页
    start = (page - 1) * PAGE_SIZE
    end = start + PAGE_SIZE

    data = []
    with open('data/amazon-reviews.csv', 'r') as file:
        reader = csv.reader(file)
        first_row = next(reader)
        for row in reader:
            photo_row = []
            for cell in row:
                if row[0] == '1':
                    row[0] = photo_row.append(url_for('static', filename='score-1.jpg'))
                elif row[0] == '2':
                    row[0] = photo_row.append(url_for('static', filename='score-2.jpg'))
                elif row[0] == '3':
                    row[0] = photo_row.append(url_for('static', filename='score-3.jpg'))
                elif row[0] == '4':
                    row[0] = photo_row.append(url_for('static', filename='score-4.jpg'))
                elif row[0] == '5':
                    row[0] = photo_row.append(url_for('static', filename='score-5.jpg'))
                else:
                    photo_row.append(cell)
            data.append(photo_row)

    total_pages = (len(data) + PAGE_SIZE - 1) // PAGE_SIZE
    paginatino_data = data[start:end]

    return render_template('reviews.html', data=paginatino_data, review_head=first_row, total_pages=total_pages, current_page=page)

@app.route('/get_city_info')
def get_city_info():
    city_name = request.args.get('city')
    print(city_name)
    city_info = ''

    with open('data/city_info.csv', 'r') as file:
        reader = csv.reader(file)
        next(reader)
        for row in reader:
            if row[0] == city_name:
                city_info = f"{city_name} is a city located in the state of {row[4]}, {row[3]}. It has a latitude of {row[1]} and a longitude of {row[2]}. The population of Pensacola is {row[5]}."
                break
    return jsonify({'city_info': city_info})


if __name__ == '__main__':
    app.run()
