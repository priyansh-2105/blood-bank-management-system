from flask import render_template, request, jsonify

def register_error_handlers(app):
    """Register error handlers for the application"""
    
    @app.errorhandler(404)
    def not_found_error(error):
        if request.accept_mimetypes.accept_json and \
           not request.accept_mimetypes.accept_html:
            return jsonify({'error': 'Not found'}), 404
        try:
            return render_template('errors/404.html'), 404
        except:
            return '<h1>Page Not Found</h1><p>The page you are looking for does not exist.</p>', 404
    
    @app.errorhandler(500)
    def internal_error(error):
        if request.accept_mimetypes.accept_json and \
           not request.accept_mimetypes.accept_html:
            return jsonify({'error': 'Internal server error'}), 500
        try:
            return render_template('errors/500.html'), 500
        except:
            return '<h1>Internal Server Error</h1><p>Something went wrong. Please try again later.</p>', 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        if request.accept_mimetypes.accept_json and \
           not request.accept_mimetypes.accept_html:
            return jsonify({'error': 'Forbidden'}), 403
        try:
            return render_template('errors/403.html'), 403
        except:
            return '<h1>Access Forbidden</h1><p>You do not have permission to access this resource.</p>', 403
    
    @app.errorhandler(401)
    def unauthorized_error(error):
        if request.accept_mimetypes.accept_json and \
           not request.accept_mimetypes.accept_html:
            return jsonify({'error': 'Unauthorized'}), 401
        try:
            return render_template('errors/401.html'), 401
        except:
            return '<h1>Unauthorized</h1><p>Please log in to access this resource.</p>', 401 