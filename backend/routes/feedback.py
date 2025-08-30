from flask import Blueprint, request, jsonify
from textblob import TextBlob

feedback_bp = Blueprint("feedback", __name__)

@feedback_bp.route("/analyze_feedback", methods=["POST"])
def analyze_feedback():
    data = request.get_json()
    feedback_text = data.get("feedback", "")

    if not feedback_text.strip():
        return jsonify({"error": "Feedback text required"}), 400

    analysis = TextBlob(feedback_text)
    polarity = analysis.sentiment.polarity

    # Convert polarity (-1 to 1) into categories
    if polarity > 0.1:
        sentiment = "positive"
    elif polarity < -0.1:
        sentiment = "negative"
    else:
        sentiment = "neutral"

    return jsonify({
        "feedback": feedback_text,
        "sentiment": sentiment,
        "polarity": polarity
    })
