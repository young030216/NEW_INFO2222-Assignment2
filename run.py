from Assignment import app

ssl_cert = '/Users/youngliang/.certs/localhost.crt'
ssl_key = '/Users/youngliang/.certs/localhost.key'

if __name__ == '__main__':
    app.run(debug=True, ssl_context=(ssl_cert,ssl_key))