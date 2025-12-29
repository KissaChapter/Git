from flask import Blueprint, make_response
from src.output.models.alert import Alert
import csv, io

bp = Blueprint('report', __name__, url_prefix='/report')

@bp.route('/csv')
def export_csv():
    si = io.StringIO()
    w = csv.writer(si)
    w.writerow(['ID','Src IP','Dst IP','Attack','Severity','Time'])
    for a in Alert.query.all():
        w.writerow([a.id, a.src_ip, a.dst_ip, a.attack_type,
                    a.severity, a.event_time.strftime('%Y-%m-%d %H:%M:%S')])
    resp = make_response(si.getvalue())
    resp.headers["Content-Disposition"] = "attachment; filename=alerts.csv"
    resp.headers["Content-type"] = "text/csv"
    return resp