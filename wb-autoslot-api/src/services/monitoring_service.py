"""
Monitoring service with Prometheus metrics
"""

import time
import psutil
import logging
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from flask import Response, current_app

logger = logging.getLogger(__name__)

class MonitoringService:
    """Service for monitoring and metrics collection"""
    
    def __init__(self):
        self.app = None
        self.start_time = time.time()
        
        # Prometheus metrics
        self.request_count = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status']
        )
        
        self.request_duration = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint']
        )
        
        self.active_tasks = Gauge(
            'active_tasks_total',
            'Number of active tasks'
        )
        
        self.found_slots = Counter(
            'slots_found_total',
            'Total number of slots found',
            ['warehouse']
        )
        
        self.wb_requests = Counter(
            'wb_requests_total',
            'Total WB API requests',
            ['status']
        )
        
        self.system_cpu = Gauge(
            'system_cpu_percent',
            'System CPU usage percentage'
        )
        
        self.system_memory = Gauge(
            'system_memory_percent',
            'System memory usage percentage'
        )
        
        self.system_disk = Gauge(
            'system_disk_percent',
            'System disk usage percentage'
        )
        
        self.database_connections = Gauge(
            'database_connections_active',
            'Number of active database connections'
        )
        
        self.worker_status = Gauge(
            'worker_running',
            'Worker running status (1=running, 0=stopped)'
        )
        
        self.notification_sent = Counter(
            'notifications_sent_total',
            'Total notifications sent',
            ['type', 'status']
        )
        
        self.rate_limit_hits = Counter(
            'rate_limit_hits_total',
            'Total rate limit hits',
            ['endpoint']
        )
    
    def init_app(self, app):
        """Initialize monitoring service with Flask app"""
        self.app = app
        
        # Register metrics endpoint
        @app.route('/metrics')
        def metrics():
            """Prometheus metrics endpoint"""
            try:
                # Update system metrics
                self._update_system_metrics()
                
                # Generate metrics response
                data = generate_latest()
                return Response(data, mimetype=CONTENT_TYPE_LATEST)
            except Exception as e:
                logger.error(f"Error generating metrics: {e}")
                return Response("Error generating metrics", status=500)
        
        # Register before_request and after_request handlers
        @app.before_request
        def before_request():
            request.start_time = time.time()
        
        @app.after_request
        def after_request(response):
            # Record request metrics
            if hasattr(request, 'start_time'):
                duration = time.time() - request.start_time
                self.request_duration.labels(
                    method=request.method,
                    endpoint=request.endpoint or 'unknown'
                ).observe(duration)
            
            self.request_count.labels(
                method=request.method,
                endpoint=request.endpoint or 'unknown',
                status=response.status_code
            ).inc()
            
            return response
    
    def _update_system_metrics(self):
        """Update system metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.system_cpu.set(cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.system_memory.set(memory.percent)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            self.system_disk.set(disk_percent)
            
        except Exception as e:
            logger.error(f"Error updating system metrics: {e}")
    
    def update_active_tasks(self, count):
        """Update active tasks count"""
        self.active_tasks.set(count)
    
    def record_slot_found(self, warehouse):
        """Record a slot found event"""
        self.found_slots.labels(warehouse=warehouse).inc()
    
    def record_wb_request(self, status):
        """Record a WB API request"""
        self.wb_requests.labels(status=status).inc()
    
    def update_worker_status(self, running):
        """Update worker running status"""
        self.worker_status.set(1 if running else 0)
    
    def record_notification_sent(self, notification_type, status):
        """Record a notification sent event"""
        self.notification_sent.labels(
            type=notification_type,
            status=status
        ).inc()
    
    def record_rate_limit_hit(self, endpoint):
        """Record a rate limit hit"""
        self.rate_limit_hits.labels(endpoint=endpoint).inc()
    
    def get_system_info(self):
        """Get current system information"""
        try:
            # System metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Process info
            process = psutil.Process()
            process_memory = process.memory_info()
            
            return {
                'system': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_used_gb': memory.used / (1024**3),
                    'memory_total_gb': memory.total / (1024**3),
                    'disk_percent': (disk.used / disk.total) * 100,
                    'disk_used_gb': disk.used / (1024**3),
                    'disk_total_gb': disk.total / (1024**3)
                },
                'process': {
                    'memory_rss_gb': process_memory.rss / (1024**3),
                    'memory_vms_gb': process_memory.vms / (1024**3),
                    'cpu_percent': process.cpu_percent(),
                    'num_threads': process.num_threads(),
                    'create_time': process.create_time()
                },
                'uptime': time.time() - self.start_time
            }
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {
                'error': str(e),
                'uptime': time.time() - self.start_time
            }
    
    def get_metrics_summary(self):
        """Get a summary of key metrics"""
        try:
            # This would need to be implemented based on your specific needs
            # For now, return basic system info
            return self.get_system_info()
        except Exception as e:
            logger.error(f"Error getting metrics summary: {e}")
            return {'error': str(e)}

# Global monitoring service instance
monitoring_service = MonitoringService()
