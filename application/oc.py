
def get_ins_office_copy(cursor, class_of_charge, reg_no, date):
    cursor.execute("SELECT ibr.request_data " +
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
        return rows[0]['request_data']