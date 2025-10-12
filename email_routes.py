from flask import Blueprint, request, jsonify, flash, redirect, url_for
from models import db, User, UserRole
from email_service import send_welcome_email
import os

email_bp = Blueprint("email", __name__)

@email_bp.route("/send_welcome_email", methods=["POST"])
def send_welcome_email_route():
    """Send a welcome email to a user"""
    try:
        email = request.form.get("email")
        name = request.form.get("name")
        
        if not email:
            return jsonify({"success": False, "error": "Email is required"}), 400
            
        # Check if user exists
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"success": False, "error": "User not found"}), 404
            
        # Send welcome email
        success = send_welcome_email(email, name)
        
        if success:
            return jsonify({"success": True, "message": "Welcome email sent successfully"})
        else:
            return jsonify({"success": False, "error": "Failed to send welcome email"}), 500
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@email_bp.route("/verify_email_token", methods=["POST"])
def verify_email_token_route():
    """Verify an email token"""
    try:
        email = request.form.get("email")
        token = request.form.get("token")
        
        if not email or not token:
            return jsonify({"success": False, "error": "Email and token are required"}), 400
            
        # Verify token
        from email_service import verify_email_token
        success = verify_email_token(email, token)
        
        if success:
            return jsonify({"success": True, "message": "Email verified successfully"})
        else:
            return jsonify({"success": False, "error": "Invalid or expired token"}), 400
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
