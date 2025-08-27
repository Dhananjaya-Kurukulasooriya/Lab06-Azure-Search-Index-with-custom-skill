import azure.functions as func
import json
import logging

app = func.FunctionApp()

@app.route(route="AnalyzeSentiment", auth_level=func.AuthLevel.FUNCTION)
def analyze_sentiment(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Hotel sentiment analysis function triggered')
    
    try:
        req_body = req.get_json()
        response = {"values": []}
        
        for record in req_body.get("values", []):
            record_id = record.get("recordId")
            data = record.get("data", {})
            
            # Get the review data from your CSV structure
            review_text = data.get("reviewText", "")
            rating = data.get("rating", 0)
            hotel_name = data.get("hotelName", "")
            
            # Analyze the review
            analysis = analyze_review_sentiment(review_text, rating, hotel_name)
            
            response["values"].append({
                "recordId": record_id,
                "data": analysis
            })
        
        return func.HttpResponse(
            json.dumps(response),
            mimetype="application/json"
        )
    
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)

def analyze_review_sentiment(review_text, rating, hotel_name):
    """Analyze sentiment of hotel review"""
    
    text = review_text.lower() if review_text else ""
    
    # Enhanced word lists for hotel reviews
    positive_words = [
        "excellent", "great", "wonderful", "amazing", "perfect", "outstanding",
        "clean", "comfortable", "beautiful", "friendly", "helpful", "fantastic",
        "lovely", "superb", "exceptional", "gorgeous", "spacious", "convenient",
        "delicious", "pleasant", "nice", "good", "satisfied", "recommend",
        "enjoyed", "relaxing", "quiet", "peaceful", "welcoming"
    ]
    
    negative_words = [
        "terrible", "awful", "dirty", "rude", "noisy", "uncomfortable", "bad",
        "poor", "disappointed", "horrible", "unacceptable", "disgusting", "worst",
        "broken", "cold", "hot", "expensive", "crowded", "small", "cramped",
        "unfriendly", "slow", "problem", "issues", "complain", "unsatisfied"
    ]
    
    # Count sentiment words
    pos_count = sum(1 for word in positive_words if word in text)
    neg_count = sum(1 for word in negative_words if word in text)
    
    # Use rating as additional sentiment indicator
    try:
        rating_num = float(rating) if rating else 0
        
        # Combine word count with rating
        if rating_num >= 4 and pos_count > neg_count:
            sentiment = "Positive"
            confidence = min(0.9, 0.6 + (pos_count * 0.05))
        elif rating_num <= 2 or neg_count > pos_count:
            sentiment = "Negative" 
            confidence = min(0.9, 0.6 + (neg_count * 0.05))
        elif rating_num == 3:
            sentiment = "Neutral"
            confidence = 0.5
        else:
            sentiment = "Positive" if pos_count > neg_count else "Negative" if neg_count > pos_count else "Neutral"
            confidence = 0.6
    except:
        sentiment = "Positive" if pos_count > neg_count else "Negative" if neg_count > pos_count else "Neutral"
        confidence = 0.5
    
    # Extract topics mentioned
    topics = []
    if any(word in text for word in ["room", "bed", "bathroom", "shower", "clean"]):
        topics.append("Room Quality")
    if any(word in text for word in ["staff", "service", "reception", "helpful", "friendly"]):
        topics.append("Service")
    if any(word in text for word in ["location", "walk", "close", "convenient"]):
        topics.append("Location")
    if any(word in text for word in ["breakfast", "food", "restaurant", "dining"]):
        topics.append("Food")
    if any(word in text for word in ["price", "value", "money", "expensive"]):
        topics.append("Value")
    
    return {
        "sentiment": sentiment,
        "confidence": round(confidence, 2),
        "topics": topics,
        "rating_based": rating_num >= 4 if rating else False
    }