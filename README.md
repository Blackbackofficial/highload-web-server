# highload-web-server

* Highload python webserver with epoll

## Requirements ##

* Respond to `GET` with status code in `{200,404,403}`
* Respond to `HEAD` with status code in `{200,404,403}`
* Respond to all other request methods with status code `405`
* Directory index file name `index.html`
* Respond to requests for `/<file>.html` with the contents of `DOCUMENT_ROOT/<file>.html`
* Requests for `/<directory>/` should be interpreted as requests for `DOCUMENT_ROOT/<directory>/index.html`
* Respond with the following header fields for all requests:
  * `Server`
  * `Date`
  * `Connection`
* Respond with the following additional header fields for all `200` responses to `GET` and `HEAD` requests:
  * `Content-Length`
  * `Content-Type`
* Respond with correct `Content-Type` for `.html, .css, js, jpg, .jpeg, .png, .gif, .swf`
* Respond to percent-encoding URLs
* Correctly serve a 2GB+ files
* No security vulnerabilities

## Run
```
docker build -t blackbackofficial .
docker run -p 80:80 -t blackbackofficial
```

## Test
```
docker build -t blackbackofficial .

git clone https://github.com/init/http-test-suite.git
cd http-test-suite

docker run -p 80:80 -v /absolute/path/to/httpd.conf:/etc/httpd.conf:ro -v /absolute/path/to/http-test-suite:/var/www/html:ro -t blackbackofficial

./httptest.py
```