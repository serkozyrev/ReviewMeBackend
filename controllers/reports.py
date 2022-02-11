from database import CursorFromConnectionFromPool
from datetime import datetime, timedelta


def all_reports():
    with CursorFromConnectionFromPool() as cursor:
        cursor.execute("SELECT r.reportid, r.reviewid, r.reporttypeid, r.comment, rw.comment,"
                       " rt.reporttype, rd.firstname ||' '|| rd.lastname,"
                       " rwd.firstname ||' '|| rwd.lastname,"
                       " rd.userid, "
                       " rwd.userid"
                       " FROM report r "
                       " INNER JOIN reporttype rt ON r.reporttypeid=rt.reporttypeid "
                       " INNER JOIN userdetails rd ON rd.userid=r.userid "
                       " INNER JOIN review rw ON rw.reviewid=r.reviewid "
                       " LEFT JOIN userdetails rwd ON rwd.userid=rw.userid "
                       " WHERE r.isactive=true")
        report_data = cursor.fetchall()
        report_list = []
        for i in range(len(report_data)):
            review_el={
                'reportid':report_data[i][0], 'reviewid':report_data[i][1], 'reportComment': report_data[i][3],
                'reviewComment':report_data[i][4], 'reporterName':report_data[i][6], 'reviewerName': report_data[i][7]
            }
            report_list.append(review_el)
        return {'reports': report_list}


def report_by_id(reportId):
    with CursorFromConnectionFromPool() as cursor:
        cursor.execute(f"select * from report r inner join reporttype rt on r.reporttypeid=rt.reporttypeid where"
                       f" r.reportid=%s and isActive=true", (reportId, ))
        report_data_by_id = cursor.fetchall()
        return {'reportsById': report_data_by_id}


def report_by_review_id(reviewId):
    with CursorFromConnectionFromPool() as cursor:
        cursor.execute(f"SELECT * FROM report WHERE reviewid=%s AND isActive=true", (reviewId, ))
        report_by_review_id = cursor.fetchall()
        return{'report_by_review': report_by_review_id}


def report_adding(userId, reviewId, date, up_date, comment, reporttypeId):
    with CursorFromConnectionFromPool() as cursor:
        cursor.execute(f"INSERT INTO report (userid, reviewid, createdate, updatedate, comment, reporttypeid, isactive)"
                       f" VALUES(%s, %s, CAST(%s AS date),"
                       f" CAST(%s AS date), %s, %s, true)", (userId, reviewId, date, up_date, comment, reporttypeId))
        return {'message': "Add report successful"}


def report_deletion(report_id, review_id):
    with CursorFromConnectionFromPool() as cursor:
        cursor.execute(f"WITH rp AS (UPDATE report SET isactive = false WHERE reportid=%s RETURNING *)"
                       f" UPDATE review rw"
                       f" SET isactive = false"
                       f" FROM rp"
                       f" WHERE rw.reviewid=%s", (report_id, review_id))
        return {'message': 'Delete Report Successful'}


def report_keeping(report_id):
    with CursorFromConnectionFromPool() as cursor:
        cursor.execute(f"UPDATE report SET isactive = false WHERE reportid = %s", (report_id,))
        return {'message': 'Keep report successful'}