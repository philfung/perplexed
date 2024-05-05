from flask import Flask, request, jsonify
from search import search_all, LIMIT_TOKENS_PER_MINUTE
from rate_limiter import RateLimiter

app = Flask(__name__)
rate_limiter = RateLimiter(LIMIT_TOKENS_PER_MINUTE)

@app.route('/search', methods=['GET'])
def search():
    user_prompt = request.args.get('question')
    if rate_limiter.is_over_limit():
        return jsonify({
            'success': False,
            'message': 'Rate limit exceeded. Please wait a minute before trying again.'
            }), 429
    else:
        response = search_all(user_prompt)
        rate_limiter.record(num_tokens=response.num_tokens_used)
        return jsonify({
            'success': True,
            'message': response.answer,
            })

if __name__ == "__main__":
    app.run(debug=True)