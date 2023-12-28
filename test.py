from azure.cosmos import CosmosClient

#
# url = "https://tutorial-uta-cse6332.documents.azure.com:443/"
# key = "fSDt8pk5P1EH0NlvfiolgZF332ILOkKhMdLY6iMS2yjVqdpWx4XtnVgBoJBCBaHA8PIHnAbFY4N9ACDbMdwaEw=="
# client = CosmosClient(url, credential=key)
# database = client.get_database_client('tutorial')
# cities = database.get_container_client('us_cities')
# reviews = database.get_container_client('reviews')
#
# # query = f"SELECT * FROM reviews WHERE reviews.city = 'Hemet'"
# query = f"SELECT * FROM c OFFSET 0 LIMIT 5"
# results = list(cities.query_items(query, enable_cross_partition_query=True))
#
# num = 0
# for result in results:
#     print(result)

if __name__ == "__main__":
    result = []
    result.append({ 'label': 'class_' + str(0 + 1), 'population': 11})
    result.append({'label': 'class_' + str(1 + 1), 'population': 1})
    print(result)
