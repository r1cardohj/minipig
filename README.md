# minipig

一个最小的WSGI服务器，仅供学习参考。


**Flask**

``` python
#flask_app.py
from flask import Flask

app = Flask(__name__)

@app.get('/')
def hello():
    return '<h1>hello Flask!</h1>
```

``` bash
python minipig.py flask_app:app
```

访问 [127.0.0.1:7777](127.0.0.1:7777)