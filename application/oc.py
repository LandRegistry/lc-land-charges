import json


def get_ins_office_copy(cursor, class_of_charge, reg_no, date):
    cursor.execute("SELECT rg.registration_no as reg_no, rg.date as registration_date, ibr.request_data " +
                   "From register rg, register_details rd, request rq, ins_bankruptcy_request ibr " +
                   "WHERE rg.registration_no=%(reg_no)s AND rg.date=%(date)s " +
                   "AND rg.details_id=rd.id " +
                   "AND rd.class_of_charge=%(class)s " +
                   "AND rd.request_id=rq.id " +
                   "AND rq.ins_request_id=ibr.id",
                   {
                       "reg_no": reg_no, "date": date, "class": class_of_charge
                   })
    rows = cursor.fetchall()
    if len(rows) == 0:
        return None
    elif len(rows) > 1:
        raise RuntimeError("Too many rows retrieved")
    else:
        data = rows[0]['request_data']
        req_data = json.loads(data)
        json_data = dict()
        json_data["request_text"] = req_data
        json_data['registration_no'] = rows[0]['reg_no']
        json_data['registration_date'] = str(rows[0]['registration_date'])
        json_data['new_registrations'] = [{"number": rows[0]['reg_no'], "date": str(rows[0]['registration_date'])}]
        return json.dumps(json_data)
