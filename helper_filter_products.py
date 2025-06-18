import json
import csv

# Read the JSON data from the file
with open('./data_examples/data.json', encoding='utf-8') as f:
    data = json.load(f)

products = data['Articulos']

preffixes = ["O02", "A414", "MP", "CMA", "FA", "MOI", "A01", "A02", "A03", "A04", "A05", "A06", "A07", "A08", "A09", "A11", "A17","A18", "A19", "A20", "A21"]

filtered_products = []

for product in products:
    for prefix in preffixes:
        if product['Codigo'].startswith(prefix):
            filtered_products.append(product)

with open('./data_examples/filtered_data.json', 'w') as p:
    json.dump(filtered_products, p, indent=2)

# Get CSV column names from first product
fieldnames = filtered_products[0].keys() if filtered_products else []


# Write to CSV
with open('./data_examples/filtered_data.csv', 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(filtered_products)