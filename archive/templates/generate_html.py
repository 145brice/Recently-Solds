import csv
import os

csv_file = 'nashville_foreclosures.csv'
html_file = 'foreclosures.html'

html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nashville Foreclosure Listings</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        a { color: #007bff; text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <h1>Nashville Foreclosure Listings</h1>
    <table>
"""

with open(csv_file, 'r') as f:
    reader = csv.reader(f)
    headers = next(reader)
    html_content += "<tr>" + "".join(f"<th>{h}</th>" for h in headers) + "</tr>\n"
    for row in reader:
        html_content += "<tr>"
        for i, cell in enumerate(row):
            if headers[i].lower() == 'link' and cell.startswith('http'):
                html_content += f"<td><a href='{cell}' target='_blank'>{cell}</a></td>"
            else:
                html_content += f"<td>{cell}</td>"
        html_content += "</tr>\n"

html_content += """
    </table>
</body>
</html>
"""

with open(html_file, 'w') as f:
    f.write(html_content)

print(f"HTML file created: {html_file}")