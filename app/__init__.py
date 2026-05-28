"""
TaskApp Application Factory.

Adds DevOps endpoints:
  - /health   → Kubernetes readiness probe (checks DB)
  - /healthz  → Kubernetes liveness probe (lightweight)
  - /metrics  → Prometheus scraping endpoint
"""
from flask import Flask, jsonify
from flask_mysqldb import MySQL
from config import Config
from prometheus_flask_exporter import PrometheusMetrics

mysql = MySQL()


def create_app():
    app = Flask(
        __name__,
        template_folder="views/templates",
        static_folder="../static",
    )
    app.config.from_object(Config)

    mysql.init_app(app)

    # ---- Prometheus metrics at /metrics ----
    metrics = PrometheusMetrics(app)
    metrics.info("app_info", "TaskApp", version="1.0.0")

    # ---- Readiness probe (checks DB connectivity) ----
    @app.route("/health")
    def health():
        try:
            with app.app_context():
                cur = mysql.connection.cursor()
                cur.execute("SELECT 1")
                cur.fetchone()
                cur.close()
            return jsonify(status="healthy", database="connected"), 200
        except Exception as e:
            return jsonify(status="unhealthy", error=str(e)), 503

    # ---- Liveness probe (just confirms app is running) ----
    @app.route("/healthz")
    def healthz():
        return jsonify(status="alive"), 200

    # ---- Register blueprints ----
    from app.controllers.task_controller import task_bp
    from app.controllers.auth_controller import auth_bp
    from app.controllers.dashboard_controller import dashboard_bp

    app.register_blueprint(task_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)

    return app
