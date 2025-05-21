import html

with open('index.html', 'r') as f:
    html_text = f.read()
    f.close()

html_text = html.unescape(html_text)

uid = "17"
digitalTwinUrl = '"http://localhost/dt-' + uid + '/chat/get"'

html_text = html_text.replace("digitalTwinUrl", digitalTwinUrl)

print(html_text)

# with open('ALICE.per-txt.txt', 'w') as f:
#     f.write(html_text)